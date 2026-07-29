"""
Agent Definitions - Agent creators and shared configuration.

This module provides re-exports of all agent creator functions from 
submodules and the main agent instructions (root agent).

Agent implementations are located in:
- app.agents.sales             → Sales Agent
- app.agents.booking           → Demo Booking Agent
- app.agents.followup          → Follow-up Agent
- app.agents.human_escalation  → Human Escalation Agent
- app.agents.lead_analysis     → Lead Analysis Agent
- app.agents.proceed_email     → Proceed Email Agent

To add a new agent:
1. Create a new submodule in app/agents/ (e.g., app/agents/my_agent/)
2. Create __init__.py with create_my_agent() function
3. Import and re-export it here in the RE-EXPORTS section
4. Add to factory.py _creators dict

Usage:
    ```python
    from app.agents.definitions import create_sales_agent
    
    sales_agent = create_sales_agent()
    ```
"""


from opik import track

from app.config.settings import logger

# =============================================================================
# RE-EXPORTS FROM AGENT SUBMODULES
# =============================================================================

from app.agents.sales import create_sales_agent, dynamic_sales_instructions
from app.agents.booking import create_demo_booking_agent, dynamic_demo_instructions
from app.agents.followup import create_followup_agent, dynamic_followup_instructions
from app.agents.human_escalation import create_human_agent, dynamic_human_instructions
from app.agents.lead_analysis import create_lead_analysis_agent
from app.agents.proceed_email import (
    create_proceed_email_agent,
    dynamic_proceed_with_email_instructions,
)
from app.agents.negotiation import create_negotiation_engine_agent, dynamic_negotiation_instructions
from app.agents.brochure import create_asset_sharing_agent, dynamic_asset_sharing_instructions
from app.agents.objection_handle import create_objection_handle_agent, dynamic_objection_handle_instructions

# =============================================================================
# MAIN AGENT INSTRUCTIONS (no subfolder for root/main agent)
# =============================================================================


@track
def dynamic_main_instructions(context, agent) -> str:
    """
    Generate dynamic instructions for main agent.

    Args:
        context: RunContextWrapper containing BotState
        agent: Agent instance

    Returns:
        Formatted prompt string for main conversation
    """
    logger.info("=" * 60)
    logger.info("[dynamic_main_instructions] Generating main agent instructions")

    try:
        from app.prompts import main_prompt

        state = context.context
        logger.info(f"User ID: {state.user_context.user_id}")
        logger.info(f"Company: {state.bot_persona.company_name}")
        logger.info(f"Agent name: {state.bot_persona.name}")
        logger.info(
            f"Chat history length: {len(state.user_context.chat_history or [])}"
        )
        logger.info(f"Last agent: {state.user_context.last_agent}")

        prompt = main_prompt(state)
        logger.info(f"Generated main prompt (first 200 chars): {prompt[:200]}...")
        logger.info("=" * 60)

        return prompt

    except Exception as e:
        logger.error(f"Error generating main instructions: {e}")
        logger.exception("Full traceback:")
        return f"You are {state.bot_persona.name}, an AI assistant for {state.bot_persona.company_name}."
