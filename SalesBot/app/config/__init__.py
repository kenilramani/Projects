"""
Configuration Package - Environment-based configuration management.

This module provides centralized configuration for the application,
supporting multiple environments (development, staging, production).

Usage:
    from app.config import settings, constants
    
    # Access settings
    database_url = settings.database_url
    
    # Access constants
    max_history = constants.MAX_HISTORY
"""

from app.config.settings import Settings, get_settings
from app.config.constants import (
    # Database
    DatabaseType,
    # Limits
    MAX_HISTORY,
    SUMMARIZE_CONTEXT_LENGTH,
    SUMMARIZE_KEEP_LAST_N_TURNS,
    # Agent names
    AgentName,
    # Booking types
    BookingType,
    # Lead classifications
    LeadClassification,
    UrgencyLevel,
)

# Global settings instance
settings = get_settings()

__all__ = [
    # Settings
    "Settings",
    "settings",
    "get_settings",
    # Constants
    "DatabaseType",
    "MAX_HISTORY",
    "SUMMARIZE_CONTEXT_LENGTH",
    "SUMMARIZE_KEEP_LAST_N_TURNS",
    "AgentName",
    "BookingType",
    "LeadClassification",
    "UrgencyLevel",
]
