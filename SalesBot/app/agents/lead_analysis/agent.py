"""
Lead Analysis Agent - Lead quality classification.

This module contains the lead analysis agent definition.
It is used as a tool within the booking agent to classify
lead quality after successful bookings.
"""

from agents import Agent


from app.config.settings import logger

from app.config.constants import AgentName


# =============================================================================
# AGENT CREATOR
# =============================================================================


def create_lead_analysis_agent() -> Agent:
    """
    Create the lead analysis agent for lead classification.

    Returns:
        Configured lead analysis Agent
    """
    from app.prompts.lead_analysis import lead_analysis_prompt
    from app.agents.config import (
        get_primary_model,
        get_model_settings,
        get_output_schema,
    )

    logger.info("Creating lead_analysis_agent")

    return Agent(
        name=AgentName.LEAD_ANALYSIS.value,
        instructions=lead_analysis_prompt,
        model=get_primary_model(),
        model_settings=get_model_settings(),
        output_type=get_output_schema(),
    )
