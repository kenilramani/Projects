"""Pipecat Quickstart Example.

The example runs a simple voice AI bot that you can connect to using your
browser and speak with it. You can also deploy this bot to Pipecat Cloud.

Required AI services:
- Deepgram (Speech-to-Text)
- OpenAI (LLM)
- Cartesia (Text-to-Speech)

Run the bot using::

    uv run bot.py
"""

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

logger.info("✅ Local Smart Turn Analyzer V3 loaded")
logger.info("Loading Silero VAD model...")
from pipecat.audio.vad.silero import SileroVADAnalyzer

logger.info("✅ Silero VAD model loaded")

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
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.turns.user_stop.turn_analyzer_user_turn_stop_strategy import (
    TurnAnalyzerUserTurnStopStrategy,
)
from pipecat.turns.user_turn_strategies import UserTurnStrategies

import os
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pipecat.services.llm_service import FunctionCallParams
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema

from calendar_service import book_demo_slot

logger.info("✅ All components loaded successfully!")

load_dotenv(override=True)

# ========================================================================
# PDF EMBEDING
# ======================================================================== 
def embed_pdf(file_path: str):
    logger.info(f"📄 Starting PDF embedding for file: {file_path}")

    logger.info(f"Loading PDF from path: {file_path}")
    loader = PyPDFLoader(file_path)
    document = loader.load()
    logger.info(f"✅ PDF loaded successfully — {len(document)} page(s) found")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunked_documents = text_splitter.split_documents(document)
    logger.info(f"✂️  Split PDF into {len(chunked_documents)} chunk(s) "
                f"(chunk_size=1000, chunk_overlap=100)")

    chroma_host = os.getenv("CHROMA_HOST")
    chroma_port = int(os.getenv("CHROMA_PORT"))
    collection_name = os.getenv("CHROMA_COLLECTION_NAME")

    logger.info(f"🔌 Connecting to ChromaDB at {chroma_host}:{chroma_port}")
    chroma_client = chromadb.HttpClient(
        host=chroma_host,
        port=chroma_port,
        settings=Settings()
    )
    logger.info(f"✅ Connected to ChromaDB at {chroma_host}:{chroma_port}")

    logger.info(f"🧠 Initializing embedding model: all-MiniLM-L6-v2")
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    logger.info(f"✅ Embedding model loaded: all-MiniLM-L6-v2")

    logger.info(f"📥 Embedding {len(chunked_documents)} chunk(s) into "
                f"collection '{collection_name}'...")
    Chroma.from_documents(
        documents=chunked_documents,
        embedding=embedding_function,
        collection_name=collection_name,
        client=chroma_client
    )
    logger.info(f"✅ Successfully embedded {len(chunked_documents)} chunk(s) "
                f"into collection '{collection_name}'")
    print("---------------------------------------------------Embedding----------------------------------------------------------------")


embed_pdf(os.getenv("file_path"))


async def query_retrieval(
        params: FunctionCallParams,
        query: str
    ):
    print("-------------------------------------------------------------------FUNCTION CALL--------------------------------------------------------------")
    logger.info(f"🔍 query_retrieval called with query: '{query}'")

    chroma_host = os.getenv("CHROMA_HOST")
    chroma_port = int(os.getenv("CHROMA_PORT"))
    collection_name = os.getenv("CHROMA_COLLECTION_NAME")

    chroma_client = chromadb.HttpClient(
        host=chroma_host,
        port=chroma_port
    )
    logger.info(f"✅ Connected to ChromaDB at {chroma_host}:{chroma_port}")

    logger.info(f"📂 Fetching collection: '{collection_name}'")
    collection = chroma_client.get_or_create_collection(
        name=collection_name
    )
    logger.info(f"✅ Fetched collection '{collection_name}' "
                f"(count: {collection.count()} document(s))")

    logger.info(f"🔎 Querying collection '{collection_name}' "
                f"with query: '{query}' | n_results=5")
    results = collection.query(
        query_texts=query,
        n_results=5
    )

    documents = results.get("documents", [])
    flattened = [doc for sublist in documents for doc in sublist]

    if not flattened:
        logger.warning(f"⚠️  No documents retrieved from collection '{collection_name}' "
                       f"for query: '{query}'")
        await params.result_callback({"result": "No relevant documents found."})
        return

    logger.info(f"📄 Retrieved {len(flattened)} chunk(s) from collection '{collection_name}'")
    for i, doc in enumerate(flattened, start=1):
        preview = doc[:80].replace("\n", " ")
        logger.debug(f"   Chunk {i}: '{preview}{'...' if len(doc) > 80 else ''}'")

    logger.info(f"✅ Returning {len(flattened)} retrieved chunk(s) to LLM")
    await params.result_callback({
        "result": "\n\n".join(flattened)
    })


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    # ========================================================================
    # TOOL
    # ========================================================================
    query_retrieval_function = FunctionSchema(
    name="query_retrieval",
    description="Search the embedded PDF knowledge base and return relevant context.",
    properties={
        "query": {
            "type": "string",
            "description": "The user question to search in the knowledge base."
        }
    },
    required=["query"],
    )

    book_demo_function = FunctionSchema(
    name="book_demo_slot",
    description="Book a product demo in Google Calendar.",
    properties={
        "name": {
            "type": "string",
            "description": "Full name of the client."
        },
        "email": {
            "type": "string",
            "description": "Email address of the client."
        },
        "date": {
            "type": "string",
            "description": "Date in YYYY-MM-DD format."
        },
        "time": {
            "type": "string",
            "description": "Time in HH:MM (24-hour format)."
        }
    },
    required=["name", "email", "date", "time"],
    )

    tools = ToolsSchema(
    standard_tools=[
        query_retrieval_function,
        book_demo_function
    ])


    logger.info(f"Starting bot")

    # ========================================================================
    # LOAD YOUR PROMPT
    # ========================================================================
    system_prompt = get_system_prompt()
    token_estimate = get_token_estimate()
    logger.info(f"📝 Loaded system prompt: ~{token_estimate:,} tokens (~{len(system_prompt):,} characters)")
    
    if token_estimate > 25000:
        logger.warning(f"⚠️  Large prompt detected! Consider enabling prompt caching to reduce costs.")
    # ========================================================================

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"),
                             language="multi",
                             detect_language=True,
                             )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="31384047-b8e2-49d5-ad3b-a48ca97e445e",
    )

    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
    )

    llm.register_direct_function(
        query_retrieval,
        cancel_on_interruption=True
    )
    async def book_demo_tool(params: FunctionCallParams, name: str, email: str, date: str, time: str):
        result = book_demo_slot(name, email, date, time)
        await params.result_callback(result)

    llm.register_direct_function(
        book_demo_tool,
        cancel_on_interruption=True
    )

    # ========================================================================
    # USE YOUR CUSTOM PROMPT HERE
    # ========================================================================

    messages = []
    context = LLMContext(messages, tools)

    context.add_message({
        "role": "system",
        "content": system_prompt
    })
    # ========================================================================

    
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            user_turn_strategies=UserTurnStrategies(
                stop=[TurnAnalyzerUserTurnStopStrategy(turn_analyzer=LocalSmartTurnAnalyzerV3())]
            ),
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
        ),
    )

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

    @transport.event_handler("on_client_connected")         # connects your browser audio to the bot
    async def on_client_connected(transport, client):
        logger.info(f"Client connected")
        # Kick off the conversation.
        context.add_message({
                "role": "system", 
                "content": "Say hello and briefly introduce yourself. Mention that you can answer questions about the uploaded document."
            })
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for the bot starter."""

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


# added calendar booking tool for demo scheduling, but testing is pending