from typing import List, Dict, Any, Optional
from app.route.route import router
from app.prompts.executive_summary_prompt import get_executive_summary_prompt
from app.utils.prompt_cache import split_direct_call_messages, cache_monitor
from opik import track


from app.config.settings import logger
from app.config.settings import Settings
Settings()


@track
async def generate_executive_summary(
    agent_result: List[Dict[str, Any]],
    chat_history: Optional[List[Dict[str, Any]]] = None,
    model: str = "summarizer",
    max_tokens: int = 500,
) -> str:
    """
    Generate an executive summary from agent_result (or chat_history as fallback).
    
    This is a standalone function with NO conditions - it generates a summary
    every time it is called. Intended to be triggered externally via API.

    Args:
        agent_result: The raw agent execution result (list of message dicts).
        chat_history: Optional fallback - used only if agent_result is empty.
        model: LLM model name to use for summarization.
        max_tokens: Maximum tokens for the LLM response.

    Returns:
        The generated executive summary string.
    """
    # Prefer agent_result; fall back to chat_history if agent_result is empty
    content = agent_result if agent_result else (chat_history or [])

    if not content:
        logger.warning("[executive_summary] No agent_result or chat_history provided. Skipping.")
        return ""

    logger.info(f"[executive_summary] Generating summary from {len(content)} items (source={'agent_result' if agent_result else 'chat_history'})")

    prompt_content = get_executive_summary_prompt(content)
    prompt_messages = split_direct_call_messages(prompt_content)

    resp = await router.acompletion(
        model=model,
        messages=prompt_messages,
        max_tokens=max_tokens,
    )

    # Record prompt cache statistics
    cache_monitor.record(resp, model=model)

    summary = resp.choices[0].message.content
    logger.info(f"[executive_summary] Summary generated successfully ({len(summary)} chars)")
    return summary
