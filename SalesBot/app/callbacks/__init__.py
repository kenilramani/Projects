"""
Callbacks Package - Handoff callback handlers for agent transitions.

This package provides callback handlers that are executed when
an agent hands off control to another agent.

Usage:
    from app.callbacks import on_sales_handoff, on_demo_handoff
    
    handoff(agent=sales_agent, on_handoff=on_sales_handoff)
"""

from app.callbacks.handlers import (
    on_sales_handoff,
    on_demo_handoff,
    on_followup_handoff,
    on_human_handoff,
)

__all__ = [
    "on_sales_handoff",
    "on_demo_handoff",
    "on_followup_handoff",
    "on_human_handoff",
]
