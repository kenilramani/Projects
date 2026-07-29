# """Pipecat Quickstart Example.

# The example runs a simple voice AI bot that you can connect to using your
# browser and speak with it. You can also deploy this bot to Pipecat Cloud.

# Required AI services:
# - Deepgram (Speech-to-Text)
# - OpenAI (LLM)
# - Cartesia (Text-to-Speech)

# Run the bot using::

#     uv run bot.py
# """

# import os

# from dotenv import load_dotenv
# from loguru import logger

# # ============================================================================
# # IMPORT YOUR PROMPT
# # ============================================================================
# from prompt import get_system_prompt, get_token_estimate

# print("🚀 Starting Pipecat bot...")
# print("⏳ Loading models and imports (20 seconds, first run only)\n")

# logger.info("Loading Local Smart Turn Analyzer V3...")
# from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3

# logger.info("✅ Local Smart Turn Analyzer V3 loaded")
# logger.info("Loading Silero VAD model...")
# from pipecat.audio.vad.silero import SileroVADAnalyzer

# logger.info("✅ Silero VAD model loaded")

# from pipecat.audio.vad.vad_analyzer import VADParams
# from pipecat.frames.frames import LLMRunFrame

# logger.info("Loading pipeline components...")
# from pipecat.pipeline.pipeline import Pipeline
# from pipecat.pipeline.runner import PipelineRunner
# from pipecat.pipeline.task import PipelineParams, PipelineTask
# from pipecat.processors.aggregators.llm_context import LLMContext
# from pipecat.processors.aggregators.llm_response_universal import (
#     LLMContextAggregatorPair,
#     LLMUserAggregatorParams,
# )
# from pipecat.runner.types import RunnerArguments
# from pipecat.runner.utils import create_transport
# from pipecat.services.cartesia.tts import CartesiaTTSService
# from pipecat.services.cartesia.stt import CartesiaSTTService
# from pipecat.services.openai.llm import OpenAILLMService
# from pipecat.transports.base_transport import BaseTransport, TransportParams
# from pipecat.transports.daily.transport import DailyParams
# from pipecat.turns.user_stop.turn_analyzer_user_turn_stop_strategy import (
#     TurnAnalyzerUserTurnStopStrategy,
# )
# from pipecat.turns.user_turn_strategies import UserTurnStrategies

# logger.info("✅ All components loaded successfully!")

# load_dotenv(override=True)


# async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
#     logger.info(f"Starting bot")

#     # ========================================================================
#     # LOAD YOUR PROMPT
#     # ========================================================================
#     system_prompt = get_system_prompt()
#     token_estimate = get_token_estimate()
#     logger.info(f"📝 Loaded system prompt: ~{token_estimate:,} tokens (~{len(system_prompt):,} characters)")
    
#     if token_estimate > 25000:
#         logger.warning(f"⚠️  Large prompt detected! Consider enabling prompt caching to reduce costs.")
#     # ========================================================================

#     # stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"),
#     #                          language="multi",
#     #                          detect_language=True,
#     #                          )
#     stt = CartesiaSTTService(api_key=os.getenv("CARTESIA_STT_API_KEY"),
#                             language="hi",   # change if needed
#                             )

#     tts = CartesiaTTSService(
#         api_key=os.getenv("CARTESIA_API_KEY"),
#         voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",  # British Reading Lady
#     )

#     llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"))

#     # ========================================================================
#     # USE YOUR CUSTOM PROMPT HERE
#     # ========================================================================
#     messages = [
#         {
#             "role": "system",
#             "content": system_prompt,
#         },
#     ]
#     # ========================================================================

#     context = LLMContext(messages)                                      # stores the full conversation history
#     user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
#         context,
#         user_params=LLMUserAggregatorParams(
#             user_turn_strategies=UserTurnStrategies(
#                 stop=[TurnAnalyzerUserTurnStopStrategy(turn_analyzer=LocalSmartTurnAnalyzerV3())]
#             ),
#             vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
#         ),
#     )

#     pipeline = Pipeline(
#         [
#             transport.input(),
#             stt,
#             user_aggregator,
#             llm,
#             tts,
#             transport.output(),
#             assistant_aggregator,
#         ]
#     )

#     task = PipelineTask(
#         pipeline,
#         params=PipelineParams(
#             enable_metrics=True,
#             enable_usage_metrics=True,
#         ),
#     )

#     @transport.event_handler("on_client_connected")         # connects your browser audio to the bot
#     async def on_client_connected(transport, client):
#         logger.info(f"Client connected")
#         # Kick off the conversation.
#         messages.append({"role": "system", "content": "Say hello and briefly introduce yourself."})
#         await task.queue_frames([LLMRunFrame()])

#     @transport.event_handler("on_client_disconnected")
#     async def on_client_disconnected(transport, client):
#         logger.info(f"Client disconnected")
#         await task.cancel()

#     runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

#     await runner.run(task)


# async def bot(runner_args: RunnerArguments):
#     """Main bot entry point for the bot starter."""

#     transport_params = {
#         "daily": lambda: DailyParams(
#             audio_in_enabled=True,
#             audio_out_enabled=True,
#         ),
#         "webrtc": lambda: TransportParams(
#             audio_in_enabled=True,
#             audio_out_enabled=True,
#         ),
#     }

#     transport = await create_transport(runner_args, transport_params)

#     await run_bot(transport, runner_args)


# if __name__ == "__main__":
#     from pipecat.runner.run import main

#     main()
    

##

import os
from dotenv import load_dotenv
from loguru import logger

# ============================================================================
# IMPORT YOUR PROMPT
# ============================================================================
from prompt import get_system_prompt, get_token_estimate

print("🚀 Starting Pipecat bot...")
print("⏳ Loading models and imports (20 seconds, first run only)\n")

logger.info("Loading Local Smart Turn Analyzer V3...")
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3

logger.info("Loading Silero VAD model...")
from pipecat.audio.vad.silero import SileroVADAnalyzer

from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame

logger.info("Loading pipeline components...")
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.cartesia.stt import CartesiaSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.turns.user_stop.turn_analyzer_user_turn_stop_strategy import (
    TurnAnalyzerUserTurnStopStrategy,
)
from pipecat.turns.user_turn_strategies import UserTurnStrategies

logger.info("✅ All components loaded successfully!")

load_dotenv(override=True)


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting bot")

    # ============================================================================
    # LOAD SYSTEM PROMPT
    # ============================================================================
    system_prompt = get_system_prompt()
    token_estimate = get_token_estimate()
    logger.info(f"📝 Loaded system prompt: ~{token_estimate:,} tokens")

    # ============================================================================
    # STT — CARTESIA
    # NOTE: Cartesia does NOT support language="multi"
    # Change language manually if required (e.g., "hi", "gu", "es")
    # ============================================================================
    stt = CartesiaSTTService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        model="sonic-3-2026-01-12"
         # Change if deploying language-specific bot
    )

    # ============================================================================
    # TTS — CARTESIA
    # ============================================================================
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="71a7ad14-091c-4e8e-a314-022ece01c121",
    )

    # ============================================================================
    # LLM — OPENAI
    # ============================================================================
    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    # ============================================================================
    # CONTEXT
    # ============================================================================
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
    ]

    context = LLMContext(messages)

    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            user_turn_strategies=UserTurnStrategies(
                stop=[
                    TurnAnalyzerUserTurnStopStrategy(
                        turn_analyzer=LocalSmartTurnAnalyzerV3()
                    )
                ]
            ),
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(stop_secs=0.4)  # slightly safer for multilingual speech
            ),
        ),
    )

    # ============================================================================
    # PIPELINE
    # ============================================================================
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    # ============================================================================
    # EVENTS
    # ============================================================================
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        messages.append(
            {
                "role": "system",
                "content": "Say hello and briefly introduce yourself.",
            }
        )
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point"""

    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
    }

    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main
    main()
