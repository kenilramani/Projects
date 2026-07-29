"""
Agent Factory - Factory pattern for creating and managing agents.

This module provides a factory class for creating agents with proper
configuration, dependency injection, and lifecycle management.

Usage:
    from app.agents.factory import AgentFactory, create_root_agent
    
    # Using factory
    factory = AgentFactory()
    sales_agent = factory.create_agent("sales")
    
    # Or use convenience function
    root_agent = create_root_agent()
"""

from typing import Callable, Dict, List, Optional, Type

from agents import Agent, AgentOutputSchema, ModelSettings, handoff


from app.config.settings import logger
from opik import track

from app.config.constants import AgentName
from app.agents.config import (
    get_primary_model,
    get_model_settings,
    get_output_guardrails,
    get_output_schema,
)
from app.agents.definitions import (
    create_sales_agent,
    create_demo_booking_agent,
    create_followup_agent,
    create_human_agent,
    create_proceed_email_agent,
    create_lead_analysis_agent,
    dynamic_main_instructions,
    create_negotiation_engine_agent,
    dynamic_negotiation_instructions,
    create_asset_sharing_agent,
    create_objection_handle_agent,
)
from app.callbacks.handlers import (
    on_sales_handoff,
    on_demo_handoff,
    on_followup_handoff,
    on_human_handoff
)

from app.core.models import BotPersona, BotState, BotResponse, HandoffArgs

class AgentFactory:
    """
    Factory for creating and managing agents.

    The AgentFactory provides:
    - Centralized agent creation with automatic caching
    - Configuration management
    - Dependency injection for tools and guardrails
    - Easy registration of new agent types

    Usage:
        ```python
        # Get the factory instance
        factory = AgentFactory()
        
        # Create agents
        sales_agent = factory.get_sales_agent()
        demo_agent = factory.get_demo_booking_agent()
        
        # Register custom agent
        factory.register_creator("custom", create_custom_agent)
        custom_agent = factory.create_agent("custom")
        ```

    Adding New Agents:
        1. Create agent definition function (e.g., `create_my_agent()`)
        2. Import it in this file
        3. Add to `_creators` dict in `__init__`
        4. Add a convenience getter method (e.g., `get_my_agent()`)

    Attributes:
        _cache: Dictionary of cached agent instances
        _creators: Dictionary mapping agent names to creator functions
    """

    def __init__(self):
        """
        Initialize the agent factory.
        
        Automatically registers all built-in agent creators.
        """
        self._cache: Dict[str, Agent] = {}
        
        # Register all built-in agent creators
        # Add new agents here by importing their creator and adding to this dict
        self._creators: Dict[str, Callable[[], Agent]] = {
            AgentName.SALES: create_sales_agent,
            AgentName.DEMO_BOOKING: create_demo_booking_agent,
            AgentName.FOLLOWUP: create_followup_agent,
            AgentName.HUMAN: create_human_agent,
            AgentName.PROCEED_EMAIL: create_proceed_email_agent,
            AgentName.LEAD_ANALYSIS: create_lead_analysis_agent,
            AgentName.NEGOTIATION_ENGINE: create_negotiation_engine_agent,
            AgentName.ASSET_SHARING: create_asset_sharing_agent,
            AgentName.OBJECTION_HANDLE: create_objection_handle_agent,
        }

        logger.debug(
            f"AgentFactory initialized with {len(self._creators)} agent types"
        )

    def create_agent(self, agent_name: str, use_cache: bool = True) -> Agent:
        """
        Create an agent by name.

        Args:
            agent_name: Name of the agent to create (use AgentName constants)
            use_cache: Whether to use cached instance if available (default: True)

        Returns:
            Agent instance

        Raises:
            ValueError: If agent_name is not recognized

        Example:
            ```python
            factory = AgentFactory()
            
            # Using constants (recommended)
            from app.config.constants import AgentName
            sales_agent = factory.create_agent(AgentName.SALES)
            
            # Using strings (works but less safe)
            demo_agent = factory.create_agent("demo_booking_agent")
            
            # Force fresh creation (bypass cache)
            fresh_agent = factory.create_agent(AgentName.SALES, use_cache=False)
            ```
        """
        # Normalize agent name
        if isinstance(agent_name, AgentName):
            agent_name = agent_name.value

        # Check cache
        if use_cache and agent_name in self._cache:
            logger.debug(f"Returning cached agent: {agent_name}")
            return self._cache[agent_name]

        # Find creator
        creator = self._creators.get(agent_name)
        if creator is None:
            available = ", ".join(self._creators.keys())
            raise ValueError(
                f"Unknown agent: '{agent_name}'. "
                f"Available agents: {available}"
            )

        # Create agent
        logger.info(f"Creating new agent: {agent_name}")
        try:
            agent = creator()
        except Exception as e:
            logger.error(f"Failed to create agent '{agent_name}': {e}")
            raise

        # Cache if enabled
        if use_cache:
            self._cache[agent_name] = agent
            logger.debug(f"Cached agent: {agent_name}")

        return agent

    def get_sales_agent(self) -> Agent:
        """Get or create the sales agent (cached)."""
        return self.create_agent(AgentName.SALES)

    def get_demo_booking_agent(self) -> Agent:
        """Get or create the demo booking agent (cached)."""
        return self.create_agent(AgentName.DEMO_BOOKING)

    def get_followup_agent(self) -> Agent:
        """Get or create the followup agent (cached)."""
        return self.create_agent(AgentName.FOLLOWUP)

    def get_human_agent(self) -> Agent:
        """Get or create the human escalation agent (cached)."""
        return self.create_agent(AgentName.HUMAN)

    def get_proceed_email_agent(self) -> Agent:
        """Get or create the proceed email agent (cached)."""
        return self.create_agent(AgentName.PROCEED_EMAIL)

    def get_negotiation_engine_agent(self) -> Agent:
        """Get or create the negotiation engine agent."""
        return self.create_agent(AgentName.NEGOTIATION_ENGINE)

    def get_asset_sharing_agent(self) -> Agent:
        """Get or create the asset sharing agent."""
        return self.create_agent(AgentName.ASSET_SHARING)

    def create_root_agent(self) -> Agent:
        """
        Create the root (main) agent with all handoffs configured.

        The root agent orchestrates conversation flow and hands off
        to specialized agents based on user intent.

        Returns:
            Configured root Agent with all handoffs and tools

        Example:
            ```python
            factory = AgentFactory()
            root = factory.create_root_agent()
            
            # Use in agent runner
            result = root.run(state)
            ```
        """
        from app.core.guardrail import input_attack

        # Create child agents
        sales_agent = self.get_sales_agent()
        demo_agent = self.get_demo_booking_agent()
        followup_agent = self.get_followup_agent()
        human_agent = self.get_human_agent()
        proceed_email_agent = self.get_proceed_email_agent()
        negotiation_engine_agent = self.get_negotiation_engine_agent()
        asset_sharing_agent = self.get_asset_sharing_agent()

        # Create proceed_with_email tool
        proceed_email_tool = proceed_email_agent.as_tool(
            tool_name="proceed_with_email",
            tool_description=(
                "Use this tool to proceed with email for further communication with the user. "
                "When user says 'continue over email', 'send me an email', 'email me the details', etc."
            ),
        )

        # Create negotiation_engine tool
        negotiation_tool = negotiation_engine_agent.as_tool(
            tool_name="negotiation_engine",
            tool_description=(
                "Use this tool to handle pricing negotiations and discounts. "
                "When user discusses pricing, asks for discounts, or negotiates pricing. "
                "Handles strategic pricing negotiation with discount management and business rules."
            ),
        )

        # Create asset_sharing tool
        asset_sharing_tool = asset_sharing_agent.as_tool(
            tool_name="proceed_with_asset_sharing",
            tool_description=(
                "Use this tool to share brochures, documents, PDFs, or files with the user. "
                "When user asks for brochure, document, catalogue, datasheet, whitepaper, "
                "or any shareable file/asset."
            ),
        )

        logger.info("Creating root agent with handoffs")

        return Agent[BotState](
            name=AgentName.MAIN.value,
            instructions=dynamic_main_instructions,
            model=get_primary_model(),
            model_settings=get_model_settings(),
            handoffs=[
                handoff(agent=sales_agent, on_handoff=on_sales_handoff, input_type=HandoffArgs),
                handoff(agent=demo_agent, on_handoff=on_demo_handoff, input_type=HandoffArgs),
                handoff(agent=followup_agent, on_handoff=on_followup_handoff, input_type=HandoffArgs),
                handoff(agent=human_agent, on_handoff=on_human_handoff, input_type=HandoffArgs),
            ],
            tools=[proceed_email_tool, negotiation_tool, asset_sharing_tool],
            input_guardrails=[input_attack],
            # output_guardrails=get_output_guardrails(),
            output_type=get_output_schema(),
        )

    def clear_cache(self):
        """Clear all cached agents."""
        self._cache.clear()
        logger.debug("Agent cache cleared")

    def register_creator(self, agent_name: str, creator: Callable[[], Agent]):
        """
        Register a custom agent creator.

        This allows extending the factory with new agent types at runtime.

        Args:
            agent_name: Name for the agent (e.g., "my_custom_agent")
            creator: Function that creates and returns the agent

        Example:
            ```python
            def create_my_agent():
                return Agent(
                    name="my_agent",
                    instructions=lambda ctx, agent: "You are helpful",
                    model=RouterModel(model="primary")
                )
            
            factory = AgentFactory()
            factory.register_creator("my_agent", create_my_agent)
            
            # Now you can create it
            my_agent = factory.create_agent("my_agent")
            ```
        """
        if agent_name in self._creators:
            logger.warning(f"Overwriting existing creator for: {agent_name}")
        
        self._creators[agent_name] = creator
        logger.debug(f"Registered creator for: {agent_name}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================
# These functions provide a simple API for creating agents without
# directly instantiating the factory. They use a global factory instance.

# Global factory instance
_factory: Optional[AgentFactory] = None


def get_factory() -> AgentFactory:
    """
    Get the global AgentFactory instance.

    Creates the factory on first call (singleton pattern).

    Returns:
        AgentFactory instance

    Example:
        ```python
        from app.agents.factory import get_factory
        
        factory = get_factory()
        sales_agent = factory.get_sales_agent()
        ```
    """
    global _factory
    if _factory is None:
        _factory = AgentFactory()
        logger.debug("Created global AgentFactory instance")
    return _factory


def create_root_agent() -> Agent:
    """
    Create the root agent with all handoffs configured.

    This is the main entry point for creating the agent system.
    Uses the global factory instance for consistency.

    Returns:
        Configured root Agent

    Example:
        ```python
        from app.agents.factory import create_root_agent
        
        root = create_root_agent()
        result = root.run(state)
        ```
    """
    return get_factory().create_root_agent()


def root_agent() -> Agent:
    """
    Alias for create_root_agent for backward compatibility.

    Returns:
        Configured root Agent
    """
    return create_root_agent()


def sales_agent() -> Agent:
    """
    Create the sales agent.
    
    Returns:
        Sales agent instance (cached)
    """
    return get_factory().get_sales_agent()


def demo_booking_agent() -> Agent:
    """
    Create the demo booking agent.
    
    Returns:
        Demo booking agent instance (cached)
    """
    return get_factory().get_demo_booking_agent()


def followup_agent() -> Agent:
    """
    Create the followup agent.
    
    Returns:
        Followup agent instance (cached)
    """
    return get_factory().get_followup_agent()


def human_agent() -> Agent:
    """
    Create the human escalation agent.
    
    Returns:
        Human escalation agent instance (cached)
    """
    return get_factory().get_human_agent()


def proceed_with_email() -> Agent:
    """
    Create the proceed with email agent.
    
    Returns:
        Proceed email agent instance (cached)
    """
    return get_factory().get_proceed_email_agent()

def negotiation_engine() -> Agent:
    """Create the negotiation engine agent."""
    return get_factory().get_negotiation_engine_agent()