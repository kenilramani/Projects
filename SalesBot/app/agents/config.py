"""
Agent Configuration - Shared configuration for all agents.

This module provides centralized configuration functions used across
all agents in the system. It ensures consistency in model settings,
guardrails, and output schemas.

Usage:
    from app.agents.config import (
        get_primary_model,
        get_model_settings,
        get_output_guardrails,
        get_output_schema,
    )
    
    agent = Agent(
        name="my_agent",
        instructions=my_instructions,
        model=get_primary_model(),
        model_settings=get_model_settings(),
        output_guardrails=get_output_guardrails(),
        output_type=get_output_schema(),
    )
"""

from typing import List

from agents import AgentOutputSchema, ModelSettings

from app.core.models import BotResponse
from app.route.route import RouterModel


# =============================================================================
# SHARED MODEL CONFIGURATION
# =============================================================================


def get_primary_model() -> RouterModel:
    """
    Get the primary RouterModel instance.
    
    This is the default model used by all agents unless overridden.
    
    Returns:
        RouterModel configured with "primary" model
    """
    return RouterModel(model="primary")


def get_model_settings() -> ModelSettings:
    """
    Get default model settings.
    
    Returns:
        ModelSettings with default configuration
    """
    return ModelSettings(prompt_cache_retention="24h")


def get_output_guardrails() -> List:
    """
    Get the output guardrail list.
    
    Output guardrails validate agent responses before returning them
    to ensure they meet quality and safety standards.
    
    Returns:
        List containing output guardrail functions
    """
    from app.core.guardrail import output_guardrail

    return [output_guardrail]


def get_output_schema() -> AgentOutputSchema:
    """
    Get the default output schema.
    
    This schema structures the agent's response into a consistent format.
    
    Returns:
        AgentOutputSchema for BotResponse model
    """
    return AgentOutputSchema(BotResponse, strict_json_schema=False)
