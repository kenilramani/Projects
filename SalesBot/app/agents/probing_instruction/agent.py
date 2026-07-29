"""
Probing Instruction Agent
=========================
Generates instruction suggestions for the probing question generation agent.
"""


from agents import Agent, Runner, set_trace_processors
from agents.extensions.models.litellm_model import LitellmModel
from opik import track
from opik.integrations.litellm import track_completion
from opik.integrations.openai.agents import OpikTracingProcessor
import litellm
from app.core.state import BotPersona
from app.core.models import InstructionAgentResponse
from app.prompts.generate_probing_instructions import (
    get_probing_instructions_agent_prompt,
)
from app.config.settings import logger
# Opik Tracing Setup
litellm.acompletion = track_completion()(litellm.acompletion)
set_trace_processors([OpikTracingProcessor()])


@track
async def generate_probing_question_instructions(
    persona: BotPersona = None, max_instructions: int = 5
):
    try:
        generate_probing_question_agent = Agent(
            name="probing_instruction_agent",
            instructions=get_probing_instructions_agent_prompt(max_instructions),
            model=LitellmModel(model="gemini/gemini-3-flash-preview"),
            output_type=InstructionAgentResponse,
        )

        agent_result = await Runner.run(
            starting_agent=generate_probing_question_agent,
            input=str(persona) if persona else "",
        )

        extracted_instructions = agent_result.final_output
        if hasattr(extracted_instructions, "model_dump"):
            extracted_instructions = extracted_instructions.model_dump()

        return {"instructions": extracted_instructions}
    except Exception as e:
        logger.error(f"Error in generate_probing_question_instructions: {e}")
        return {"error": str(e), "instructions": []}