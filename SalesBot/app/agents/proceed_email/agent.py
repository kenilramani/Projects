"""
Proceed Email Agent - Email communication flow.

This module contains the proceed-with-email agent definition including:
- Dynamic instruction generator
- Agent creator function
"""

from agents import Agent


from app.config.settings import logger
from opik import track

from app.config.constants import AgentName


# =============================================================================
# DYNAMIC INSTRUCTION GENERATOR
# =============================================================================


@track
def dynamic_proceed_with_email_instructions(context, agent) -> str:
    """
    Generate dynamic instructions for proceed with email agent.

    Args:
        context: RunContextWrapper containing BotState
        agent: Agent instance

    Returns:
        Formatted prompt string for email flow
    """
    logger.info("=" * 60)
    logger.info(
        "[dynamic_proceed_with_email_instructions] Generating proceed with email instructions"
    )

    try:
        from app.prompts import proceed_with_email_prompt

        state = context.context
        logger.info(f"Bot state type: {type(state)}")

        prompt = proceed_with_email_prompt(state)
        logger.info(
            f"Generated proceed with email prompt (first 200 chars): {prompt[:200]}..."
        )
        logger.info("=" * 60)

        return prompt

    except Exception as e:
        logger.error(f"Error generating proceed with email instructions: {e}")
        logger.exception("Full traceback:")
        return "You are a proceed with email assistant. Help schedule future interactions with the user."


# =============================================================================
# AGENT CREATOR
# =============================================================================


def create_proceed_email_agent() -> Agent:
    """
    Create the proceed with email agent.

    Returns:
        Configured proceed email Agent
    """
    from app.agents.config import (
        get_primary_model,
        get_model_settings,
        get_output_schema,
    )

    return Agent(
        name=AgentName.PROCEED_EMAIL.value,
        instructions=dynamic_proceed_with_email_instructions,
        model=get_primary_model(),
        model_settings=get_model_settings(),
        output_type=get_output_schema(),
    )
