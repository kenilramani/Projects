"""Template Generation Agent Package."""

from app.agents.template_generation.agent import (
    run_template_generation_agent,
    get_template_generation_agent_prompt,
)

__all__ = ["run_template_generation_agent", "get_template_generation_agent_prompt"]
