import os
import litellm
from litellm import Router
from opik.integrations.litellm import track_completion
from agents.extensions.models.litellm_model import LitellmModel
from typing import Any, AsyncIterator
from agents.model_settings import ModelSettings
from agents.tool import Tool
from agents.handoffs import Handoff
from agents.models.interface import ModelTracing
from agents.items import TResponseInputItem, TResponseStreamEvent
from agents.agent_output import AgentOutputSchemaBase
from agents.models.chatcmpl_converter import Converter

# Import settings from config
from app.config import settings

# Import prompt cache utilities
from app.utils.prompt_cache import split_cached_prompt, cache_monitor

# Model name configuration from settings
PRIMARY_MODEL = settings.primary_model                         # azure/gpt-5.1-chat
GUARDRAIL_MODEL = settings.guardrail_model                     # azure/gpt-4.1-nano
SUMMARIZER_MODEL = settings.summarizer_model                   # azure/gpt-4.1-nano
OPENAI_FALLBACK_PRIMARY_MODEL = settings.openai_fallback_primary_model    # gpt-5.1-chat-latest
OPENAI_FALLBACK_GUARDRAIL_MODEL = settings.openai_fallback_guardrail_model  # gpt-4.1-nano
OPENAI_FALLBACK_SUMMARIZER_MODEL = settings.openai_fallback_summarizer_model  # gpt-4.1-nano
GEMINI_FALLBACK_MODEL = settings.gemini_fallback_model         # gemini/gemini-3-flash-preview


def _is_gpt5_model(model_name: str) -> bool:
    """Check if the model is a GPT-5 family model that supports reasoning_effort."""
    model_lower = model_name.lower()
    return "gpt-5" in model_lower or "gpt5" in model_lower


def _build_azure_primary_litellm_params() -> dict:
    """Build litellm_params for Azure primary model (gpt-5.1-chat) with conditional reasoning support."""
    params = {
        "model": PRIMARY_MODEL,
        "api_key": settings.azure_openai_key,
        "api_base": settings.azure_openai_endpoint,
        "api_version": settings.azure_api_version,
        "base_model": settings.azure_openai_model_name,   # e.g. "gpt-5.1-chat" for cost/token tracking
        "drop_params": True,
    }

    if _is_gpt5_model(PRIMARY_MODEL):
        params["reasoning_effort"] = "medium"
    else:
        params["temperature"] = 0.7

    return params


def _build_azure_nano_litellm_params(model_name: str) -> dict:
    """Build litellm_params for Azure gpt-4.1-nano models (guardrail & summarizer)."""
    return {
        "model": model_name,
        "api_key": settings.azure_openai_key,
        "api_base": settings.azure_openai_endpoint,
        "api_version": settings.azure_nano_api_version,
        "base_model": "gpt-4.1-nano",   # for accurate cost/token tracking
        "drop_params": True,
    }


def _build_openai_fallback_primary_params() -> dict:
    """Build litellm_params for OpenAI fallback primary model."""
    params = {
        "model": OPENAI_FALLBACK_PRIMARY_MODEL,
        "api_key": settings.openai_api_key,
    }

    if _is_gpt5_model(OPENAI_FALLBACK_PRIMARY_MODEL):
        params["reasoning_effort"] = "medium"
    else:
        params["temperature"] = 0.7

    return params


# 1. Define Model List (Migrated from config.yaml)
# Primary models: Azure  |  Fallback: OpenAI  |  Final fallback: Gemini
MODEL_LIST = [
    # ── Azure primary models ──────────────────────────────────────────
    {
        "model_name": "primary",
        "litellm_params": _build_azure_primary_litellm_params(),
    },
    {
        "model_name": "guardrail",
        "litellm_params": _build_azure_nano_litellm_params(GUARDRAIL_MODEL),
    },
    {
        "model_name": "summarizer",
        "litellm_params": _build_azure_nano_litellm_params(SUMMARIZER_MODEL),
    },
    # ── OpenAI fallback models (role-specific) ────────────────────────
    {
        "model_name": "fallback-primary",
        "litellm_params": _build_openai_fallback_primary_params(),
    },
    {
        "model_name": "fallback-guardrail",
        "litellm_params": {
            "model": OPENAI_FALLBACK_GUARDRAIL_MODEL,
            "api_key": settings.openai_api_key,
        },
    },
    {
        "model_name": "fallback-summarizer",
        "litellm_params": {
            "model": OPENAI_FALLBACK_SUMMARIZER_MODEL,
            "api_key": settings.openai_api_key,
        },
    },
    # ── Gemini final fallback ─────────────────────────────────────────
    {
        "model_name": "fallback-gemini",
        "litellm_params": {
            "model": GEMINI_FALLBACK_MODEL,
            "api_key": settings.gemini_api_key,
        },
    },
]

# 2. Define Router Settings
LITELLM_SETTINGS = {
    "num_retries": 0,
    "timeout": 30,  # Router uses 'timeout' not 'request_timeout'
}

# Set global allowed fallback errors
litellm.allowed_fallback_errors = [
    "rate_limit",
    "insufficient_quota",
    "timeout",
    "internal_server_error",
    "bad_gateway",
    "service_unavailable",
    "context_length_exceeded",
    "authentication_error",
    "invalid_request_error",
    "unauthorized_error",
    "forbidden_error",
    "not_found_error",
    "authentication",
    "invalid_api_key",
    "AuthenticationError",
]

# 3. Define Fallback Strategy (role-specific)
# primary (Azure) → fallback-primary (OpenAI) → fallback-gemini (Gemini)
# guardrail (Azure) → fallback-guardrail (OpenAI) → fallback-gemini
# summarizer (Azure) → fallback-summarizer (OpenAI) → fallback-gemini
FALLBACKS = [
    {"primary": ["fallback-primary", "fallback-gemini"]},
    {"guardrail": ["fallback-guardrail", "fallback-gemini"]},
    {"summarizer": ["fallback-summarizer", "fallback-gemini"]},
    {"fallback-primary": ["fallback-gemini"]},
    {"fallback-guardrail": ["fallback-gemini"]},
    {"fallback-summarizer": ["fallback-gemini"]},
]

# 4. Initialize Router
router = Router(model_list=MODEL_LIST, fallbacks=FALLBACKS, **LITELLM_SETTINGS)

# 5. Patch Router for Opik Tracing
# router.acompletion = track_completion()(router.acompletion)


# 6. Implement RouterModel for Agents SDK
class RouterModel(LitellmModel):
    """
    A custom model class that uses a global litellm.Router.
    """

    def __init__(self, model: str):
        super().__init__(model=model)

    async def _fetch_response(
        self,
        system_instructions: str | None,
        input: str | list[TResponseInputItem],
        model_settings: ModelSettings = ModelSettings(prompt_cache_retention="24h"),
        tools: list[Tool] | None = None,  
        output_schema: AgentOutputSchemaBase | None = None,
        handoffs: list[Handoff] | None = None,
        span: Any | None = None,  # Span[GenerationSpanData]
        tracing: ModelTracing | None = None,
        stream: bool = False,
        prompt: Any | None = None,
    ):
        """
        Override to use the global router instead of direct litellm.acompletion.
        """
        import time
        from agents.extensions.models.litellm_model import (
            LitellmConverter,
            FAKE_RESPONSES_ID,
            Response,
            OpenAIResponsesConverter,
            omit,
        )
        from litellm.types.utils import ModelResponse as LiteLLMModelResponse

        converted_messages = Converter.items_to_messages(
            input, preserve_thinking_blocks=(model_settings.reasoning is not None)
        )

        # Split system instructions for prompt prefix caching
        # Static content becomes the first system message (cached by OpenAI)
        # Dynamic content becomes the second system message (not cached)
        if system_instructions:
            if settings.enable_prompt_caching:
                static_part, dynamic_part = split_cached_prompt(system_instructions)
                if dynamic_part:
                    # Insert dynamic context first (will be pushed to index 1)
                    converted_messages.insert(
                        0, {"role": "system", "content": dynamic_part}
                    )
                    # Insert static instructions at index 0 (cached prefix)
                    converted_messages.insert(
                        0, {"role": "system", "content": static_part}
                    )
                else:
                    converted_messages.insert(
                        0, {"role": "system", "content": system_instructions}
                    )
            else:
                converted_messages.insert(
                    0, {"role": "system", "content": system_instructions}
                )

        converted_tools = [Converter.tool_to_openai(t) for t in tools] if tools else []
        for h in handoffs:
            converted_tools.append(Converter.convert_handoff_tool(h))

        extra_kwargs = {}
        if model_settings.extra_args and model_settings.extra_args is not omit:
            extra_kwargs = model_settings.extra_args.copy()

        # Handle structured output schema
        if output_schema is not None:
            json_schema = output_schema.json_schema()
            extra_kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "output",
                    "schema": json_schema,
                    "strict": output_schema.is_strict_json_schema(),
                },
            }

        # Use the router instead of litellm.acompletion
        ret = await router.acompletion(
            model=self.model,
            messages=converted_messages,
            tools=converted_tools if converted_tools else None,
            tool_choice=self._remove_not_given(
                OpenAIResponsesConverter.convert_tool_choice(model_settings.tool_choice)
            ),
            max_tokens=self._remove_not_given(model_settings.max_tokens),
            temperature=self._remove_not_given(model_settings.temperature),
            top_p=self._remove_not_given(model_settings.top_p),
            stream=stream,
            **extra_kwargs,
        )

        if isinstance(ret, LiteLLMModelResponse):
            # Record prompt cache statistics from response
            cache_monitor.record(ret, model=self.model)
            return ret

        responses_tool_choice = OpenAIResponsesConverter.convert_tool_choice(
            model_settings.tool_choice
        )
        if responses_tool_choice is None or responses_tool_choice is omit:
            responses_tool_choice = "auto"

        response = Response(
            id=FAKE_RESPONSES_ID,
            created_at=time.time(),
            model=self.model,
            object="response",
            output=[],
            tool_choice=responses_tool_choice,  # type: ignore
            top_p=model_settings.top_p,
            temperature=model_settings.temperature,
            tools=[],
            parallel_tool_calls=model_settings.parallel_tool_calls or False,
            reasoning=model_settings.reasoning,
        )
        return response, ret

    def _remove_not_given(self, value: Any) -> Any:
        from openai import NotGiven
        from agents.extensions.models.litellm_model import omit

        if value is omit or isinstance(value, NotGiven):
            return None
        return value
