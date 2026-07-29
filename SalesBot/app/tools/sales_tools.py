"""
This module contains tools for the Agents application.
"""

from agents import function_tool, RunContextWrapper
from typing import Optional
from rag.retriever.retriever import Retriever


from app.config.settings import logger
from datetime import datetime
import pytz
from pydantic import BaseModel
import os
from app.core.request_context import get_current_user_id
from app.core.state import BotState
class LocalToUTCInput(BaseModel):
    local_time_str: str
    timezone: str

from app.config.settings import Settings
Settings()

@function_tool
def retrieve_query(ctx: RunContextWrapper[BotState], user_query: str) -> str:
    # Get tenant_id from the state context
    state: BotState = ctx.context
    
    try:
        tenant_id = state.user_context.tenant_id
        logger.info(f"Using collection/tenant_id: {tenant_id}")
    except Exception as e:
        logger.error(f"Error retrieving tenant_id from context: {e}")
    

    logger.info(
        "*********************************** Tool calling *********************************************"
    )
    results = Retriever().retrieve(
        query=user_query,
        tenant_id=tenant_id,
        kb_ids=None,
    )
    return results
