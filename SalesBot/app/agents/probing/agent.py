"""
Probing Agent - Generates probing questions for persona refinement.

This agent generates probing questions based on the current
BotPersona to gather additional information from the user.
"""

from agents import Agent, ModelSettings, Runner, RunContextWrapper
import os
from app.core.state import (
    BotPersona,
    ProbingAgentRequest,
    ProbingAgentResponse,
    ProbingQuestion,
    Products,
)



from app.config.settings import logger
from opik import track

from app.route.route import RouterModel
from app.prompts import dynamic_probing_instructions
from app.config.settings import Settings
Settings()

# Load environment variables
# os.getenv("OPENAI_API_KEY")
Settings().openai_api_key

# OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME") or ""
OPENAI_MODEL_NAME = Settings().openai_model_name


# Define models using the centralized RouterModel from route.py
primary_model = RouterModel(model="primary")
fallback_model = RouterModel(model="fallback-primary")

# Fallback settings are now managed by the Router in route.py
primary_settings = ModelSettings(prompt_cache_retention="24h")
fallback_settings = ModelSettings(prompt_cache_retention="24h")


def get_probing_agent(persona):
    return Agent(
        name="probing_agent",
        instructions=dynamic_probing_instructions(persona),
        model=primary_model,
        model_settings=primary_settings,
        output_type=ProbingAgentResponse,
    )


@track
async def run_probing_agent(persona: BotPersona, total_k: int = 5, comment: str = ""):
    try:
        logger.info("|" * 60)
        logger.info(f"Starting Probing Agent with request: {persona}")
        logger.info("|" * 60)
        result = await Runner.run(
            starting_agent=get_probing_agent(persona),
            input=f"total_k {total_k}, comment: {comment}",
            context=RunContextWrapper(persona),
        )
        logger.info("|" * 60)
        logger.info(f"Result of Probing Agent: {result}")
        logger.info("|" * 60)

        output_data = {}
        if hasattr(result.final_output, "model_dump"):
            output_data = result.final_output.model_dump(exclude_unset=True)
        elif hasattr(result.final_output, "__dict__"):
            output_data = {
                k: v for k, v in result.final_output.__dict__.items() if v is not None
            }

        logger.info("|" * 60)
        logger.info(f"Extracted Result from Probing Agent Respnse: {output_data}")
        logger.info("|" * 60)

        questions = output_data.get("questions", [])
        logger.info("|" * 60)
        logger.info(f"Questions: \n{questions}")
        logger.info("|" * 60)

        return questions
    except Exception as e:
        logger.error(f"Error Generating Probing Questions: {e}")
        logger.exception("Full traceback:")
        return {"error": f"Error Generating Probing Questions : {str(e)}"}
