"""
Booking Agent - Demo scheduling, rescheduling, and cancellation.

This module contains the booking agent definition including:
- Dynamic instruction generator for demo booking
- Agent creator function

Related agents (lead_analysis, proceed_email) are in their own subfolders.
Tools are imported from app.tools (not moved here).
"""

from agents import Agent


from app.config.settings import logger
from opik import track

from app.config.constants import AgentName


# =============================================================================
# DYNAMIC INSTRUCTION GENERATOR
# =============================================================================


@track
def dynamic_demo_instructions(context, agent) -> str:
    """
    Generate dynamic instructions for demo booking agent.

    Handles:
    - New booking requests
    - Rescheduling existing bookings
    - Cancellation requests
    - Lead quality analysis after successful bookings

    Args:
        context: RunContextWrapper containing BotState
        agent: Agent instance

    Returns:
        Formatted prompt string for demo booking
    """
    logger.info("=" * 60)
    logger.info("[dynamic_demo_instructions] Generating demo booking instructions")

    try:
        from app.prompts import demo_prompt

        state = context.context
        logger.info(f"User ID: {state.user_context.user_id}")
        logger.info(f"Collected fields: {state.user_context.collected_fields}")
        logger.info(f"Booking confirmed: {state.user_context.booking_confirmed}")
        logger.info(f"Booking type: {state.user_context.booking_type}")

        prompt = demo_prompt(state)
        logger.info(f"Generated demo prompt (first 200 chars): {prompt[:200]}...")
        logger.info("=" * 60)

        return prompt

    except Exception as e:
        logger.error(f"Error generating demo instructions: {e}")
        logger.exception("Full traceback:")
        return (
            "You are a demo booking assistant. Help the user schedule a product demonstration. "
            "Use available tools for datetime validation and calendly checking."
        )


# =============================================================================
# AGENT CREATOR
# =============================================================================


def create_demo_booking_agent() -> Agent:
    """
    Create the demo booking agent with comprehensive booking workflow support.

    Capabilities:
    - NEW BOOKING: Collects email, date, time, product with validation
    - RESCHEDULE: Changes date/time for existing confirmed bookings
    - CANCEL: Handles cancellation of confirmed bookings
    - LEAD ANALYSIS: Analyzes lead quality after successful bookings

    Tools:
    - get_timezone: Detects user timezone
    - process_booking_datetime: UNIFIED tool that parses datetime expressions, validates
      against business rules, and converts to UTC in a single call
    - check_calendly_availability: Checks Calendly for slot availability
    - lead_analysis_tool: Analyzes lead quality after successful bookings

    Returns:
        Configured demo booking Agent
    """
    from app.tools.followup_timezone import get_timezone
    from app.tools.booking_tools import (
        process_booking_datetime,  # Unified datetime processing tool
        check_calendly_availability,
    )
    from app.agents.lead_analysis import create_lead_analysis_agent
    from app.agents.config import (
        get_primary_model,
        get_model_settings,
        get_output_schema,
    )

    # Create lead analysis as a tool
    lead_analysis_tool = create_lead_analysis_agent().as_tool(
        tool_name="lead_analysis_tool",
        tool_description=(
            "Use this tool when booking is confirmed and booking type is not 'cancel'. "
            "Analyze lead quality based on conversation history and contact details. "
            "Return classification: 'hot' (high urgency, eager), 'warm' (engaged, considering), "
            "or 'cold' (minimal engagement). Consider eagerness, urgency, specific needs, "
            "and engagement level to prioritize follow-up."
        ),
    )

    return Agent(
        name=AgentName.DEMO_BOOKING.value,
        handoff_description=(
            "Used for handling user's query when user wants to book a demo, engage in "
            "conversational lead collection, OR is providing booking details (email, timezone, "
            "date, time) for a demo. Hand off when user says 'book a demo', 'schedule a call', "
            "'arrange a meeting', 'reschedule', 'cancel demo', shows interest in product/service "
            "after probing is complete (conversational CTA), or responds to questions from this "
            "agent (e.g., provides an email, date, or says 'sure', 'yes', 'okay')."
        ),
        instructions=dynamic_demo_instructions,
        model=get_primary_model(),
        model_settings=get_model_settings(),
        tools=[
            get_timezone,
            process_booking_datetime,
            lead_analysis_tool,
            check_calendly_availability,
        ],
        # output_guardrails=get_output_guardrails(), # commented out for now
        output_type=get_output_schema(),
    )
