"""
Template Generation Agent
=========================
Generates WhatsApp message templates based on the bot persona.
"""


from agents import Agent, Runner, set_trace_processors
from agents.extensions.models.litellm_model import LitellmModel
from opik import track
from opik.integrations.litellm import track_completion
from opik.integrations.openai.agents import OpikTracingProcessor
import litellm

# Import from project modules
from app.core.state import BotPersona, TemplateGenerationResponse
from app.prompts.template_generation import get_template_generation_agent_prompt

# ---------------------------------------------------------------------------
# Opik Tracing Setup
# ---------------------------------------------------------------------------
litellm.acompletion = track_completion()(litellm.acompletion)
set_trace_processors([OpikTracingProcessor()])


# ---------------------------------------------------------------------------
# Main Agent Function
# ---------------------------------------------------------------------------
@track
async def run_template_generation_agent(
    persona: BotPersona = None, max_products: int = 1
):

    try:
        generate_templates = Agent(
            name="template_generation_agent",
            instructions=get_template_generation_agent_prompt(max_products),
            model=LitellmModel(model="gemini/gemini-3-flash-preview"),
            output_type=TemplateGenerationResponse,
        )

        agent_result = await Runner.run(
            starting_agent=generate_templates, input=str(persona) if persona else ""
        )

        extracted_templates = agent_result.final_output
        if hasattr(extracted_templates, "model_dump"):
            extracted_templates = extracted_templates.model_dump()

        return extracted_templates
    except Exception as e:
        # logging.error(f"Error in run_template_generation_agent: {e}")
        # Assuming there is a logger in this file, but looking at file content I didn't see one initialized.
        # I will print for now or just return error.
        print(f"Error in run_template_generation_agent: {e}") 
        return {"error": str(e), "templates": []}
