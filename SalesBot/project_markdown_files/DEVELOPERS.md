# BotRunner Developer Guide

> **Last Updated:** March 6, 2026 &nbsp;|&nbsp; **Version:** 2.1.0  
> **Audience:** Backend Developers, DevOps, Contributors

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
  - [Required Variables](#required-variables)
  - [Optional Variables](#optional-variables)
  - [Model Configuration](#model-configuration)
  - [Database Configuration](#database-configuration)
  - [Session Configuration](#session-configuration)
  - [RAG Configuration](#rag-configuration)
  - [Observability](#observability)
- [Running the Application](#running-the-application)
  - [Development Server](#development-server)
  - [Streamlit Admin Panel](#streamlit-admin-panel)
  - [Production Server](#production-server)
- [Testing](#testing)
- [Adding a New Agent](#adding-a-new-agent)
- [Adding a New Tool](#adding-a-new-tool)
- [Adding a New Prompt](#adding-a-new-prompt)
- [Database Migrations](#database-migrations)
- [RAG Pipeline Operations](#rag-pipeline-operations)
- [Debugging & Tracing](#debugging--tracing)
- [Common Issues](#common-issues)
- [Contribution Guidelines](#contribution-guidelines)

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | >= 3.10 |
| uv (recommended) | latest |
| pip | >= 22.0 (alternative to uv) |
| Git | any |
| Node.js | Not required |

**API accounts needed:**
- Azure OpenAI (primary LLM) — or OpenAI API key for fallback
- Qdrant Cloud (production vector DB) — or run locally
- Opik account (observability) — optional

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd botrunner

# 2. Create virtual environment (using uv)
uv venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/macOS

# 3. Install dependencies
uv sync
# OR with pip:
# pip install -e .

# 4. Create .env file (copy from example and fill in values)
cp .env_example .env
# Edit .env with your API keys

# 5. Start the development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 6. Test it works
curl http://localhost:8000/health
# → {"status": "healthy"}

# 7. Send a test message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_context": {"user_id": "test", "tenant_id": "dev", "user_query": "Hi"}}'
```

---

## Project Structure

```
botrunner/
├── main.py                  # FastAPI app + 10 endpoints
├── app_agent.py             # 10-step execution pipeline
├── pyproject.toml           # Dependencies and build config
├── .env                     # Environment variables (not in git)
│
├── app/                     # Main application package
│   ├── agents/              # Agent definitions & factory
│   │   ├── factory.py       # AgentFactory — creates root agent
│   │   ├── definitions.py   # Re-exports all agent creators
│   │   ├── config.py        # Shared model/config functions
│   │   ├── booking/         # Demo booking agent
│   │   ├── brochure/        # Asset sharing agent
│   │   ├── crawl_persona/   # Website crawl → persona agent
│   │   ├── followup/        # Follow-up agent
│   │   ├── human_escalation/# Human handoff agent
│   │   ├── lead_analysis/   # Lead classification agent
│   │   ├── negotiation/     # Pricing negotiation agent
│   │   ├── objection_handle/# Objection handling agent
│   │   ├── probing/         # Probing question generator
│   │   ├── probing_instruction/ # Probing instruction generator
│   │   ├── proceed_email/   # Email switch agent
│   │   ├── sales/           # Sales/product info agent
│   │   └── template_generation/ # WhatsApp template generator
│   │
│   ├── callbacks/           # Handoff callback functions
│   │   └── handlers.py      # on_sales_handoff, on_demo_handoff, etc.
│   │
│   ├── config/              # Configuration
│   │   ├── settings.py      # Settings(BaseSettings) — env vars
│   │   └── constants.py     # AgentName enum, defaults
│   │
│   ├── core/                # Core domain logic
│   │   ├── models.py        # All Pydantic models (1600+ lines)
│   │   ├── guardrail.py     # Input/output guardrails
│   │   ├── probing_state.py # Probing engine state machine
│   │   ├── negotiation.py   # Negotiation engine (protected fields)
│   │   ├── request_context.py # Thread-local request context
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── state.py         # Backward compatibility re-exports
│   │
│   ├── database/            # Data persistence
│   │   ├── session_manager.py    # SQLite session CRUD
│   │   ├── postgresql_session_manager.py # Neon PG sessions
│   │   ├── cachememory.py        # Semantic cache
│   │   ├── summarizer.py        # Conversation summarizer
│   │   ├── sliding_window.py    # History windowing
│   │   ├── executive_summary.py # Executive summary gen
│   │   └── models.py            # SQLAlchemy ORM models
│   │
│   ├── instructions/        # Instruction generators
│   ├── prompts/             # Dynamic prompt templates
│   ├── route/               # LLM routing (LiteLLM Router)
│   │   └── route.py         # RouterModel, MODEL_LIST, FALLBACKS
│   │
│   ├── tools/               # Agent tools
│   │   └── booking_tools.py # Datetime parsing, Calendly, email validation
│   │
│   └── utils/               # Utilities
│       ├── utils.py          # convert_to_botstate, model_to_dict
│       └── prompt_cache.py   # Prompt caching utilities
│
├── rag/                     # RAG pipeline (independent module)
│   ├── main_runner.py       # RAG entry point
│   ├── ETL_Pipeline/        # Document ingestion
│   ├── Qdrant/              # Vector DB operations
│   └── retriever/           # Search + reranking
│
├── streamlit_ui/            # Admin panel
│   ├── app.py               # Main Streamlit app
│   └── ...
│
├── data/                    # Static data files
├── docs/                    # Documentation
└── tests/                   # Test files
```

---

## Environment Variables

Create a `.env` file in the project root. The application uses Pydantic `BaseSettings` to load and validate all environment variables.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | `sk-abc123...` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://my-resource.openai.azure.com/` |
| `OPENAI_API_KEY` | OpenAI API key (fallback) | `sk-xyz789...` |

> At minimum, you need **either** `AZURE_OPENAI_KEY` + `AZURE_OPENAI_ENDPOINT` **or** `OPENAI_API_KEY` for the system to function.

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development`, `staging`, `production`, `testing` |
| `DEBUG` | `false` | Enable debug logging |

### Model Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PRIMARY_MODEL` | `azure/gpt-5.1-chat` | Primary chat model |
| `GUARDRAIL_MODEL` | `azure/gpt-4.1-nano` | Model for input/output guardrails |
| `SUMMARIZER_MODEL` | `azure/gpt-4.1-nano` | Model for summarization |
| `AZURE_API_VERSION` | `2025-03-01-preview` | Azure OpenAI API version |
| `AZURE_NANO_API_VERSION` | `2025-01-01-preview` | Azure API version for nano models |
| `OPENAI_FALLBACK_PRIMARY_MODEL` | `gpt-5.1-chat-latest` | OpenAI fallback for primary |
| `OPENAI_FALLBACK_GUARDRAIL_MODEL` | `gpt-4.1-nano` | OpenAI fallback for guardrail |
| `OPENAI_FALLBACK_SUMMARIZER_MODEL` | `gpt-4.1-nano` | OpenAI fallback for summarizer |
| `GEMINI_FALLBACK_MODEL` | `gemini/gemini-3-flash-preview` | Gemini final fallback |
| `GEMINI_API_KEY` | — | Google Gemini API key (for final fallback) |
| `ENABLE_PROMPT_CACHING` | `true` | Enable prompt prefix caching optimization |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE` | `SQLite` | Database type: `SQLite` or `neon` |
| `DATABASE_URL` | — | PostgreSQL connection string (for `neon`) |
| `SQLALCHEMY_DATABASE_URL` | `:memory:` | SQLAlchemy URL for agent sessions |
| `SESSIONS_ID` | `global_runner_session` | Session identifier for SQLAlchemy |
| `ENABLE_SESSION_CREATION_TABLES` | `true` | Auto-create session tables |
| `SESSION_CONTEXT_WINDOW_SIZE` | `10` | Agent SDK session context window |

### Session Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_HISTORY` | `15` | Maximum chat_history messages before summarization |
| `SUMMARIZE_CONTEXT_LENGTH` | `3` | Context length for summarization |
| `SUMMARIZE_KEEP_LAST_N_TURNS` | `3` | Number of recent turns to keep unsummarized |

### RAG Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_URL` | — | Qdrant server URL |
| `QDRANT_API_KEY` | — | Qdrant API key |
| `QDRANT_HOST` | — | Qdrant host (alternative to URL) |
| `QDRANT_PORT` | — | Qdrant port |
| `AZURE_EMBED_ENDPOINT` | — | Azure embedding endpoint |
| `AZURE_INFERENCE_CREDENTIAL` | — | Azure inference credential |
| `AZURE_EMBED_DEPLOYMENT` | — | Azure embed deployment name |
| `AZURE_EMBED_MODEL` | — | Azure embed model name |
| `EMBEDDING_MODEL` | — | Embedding model identifier |
| `AZURE_CROSS_ENCODER_ENDPOINT` | — | Cross-encoder reranker endpoint |
| `AZURE_CROSS_ENCODER_CREDENTIAL` | — | Cross-encoder credential |
| `COHERE_RERANKER_API_KEY` | — | Cohere reranker API key |
| `COHERE_URL` | — | Cohere API URL |

### Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `OPIK_PROJECT_NAME` | — | Opik project name for tracing |
| `OPIK_WORKSPACE` | — | Opik workspace identifier |

---

## Running the Application

### Development Server

```bash
# Standard (with auto-reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# With specific log level
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

# Custom port
uvicorn main:app --host 0.0.0.0 --port 9000 --reload
```

The server starts with:
- SQLite in-memory database initialized at startup
- Interactive API docs at `http://localhost:8000/docs`
- ReDoc at `http://localhost:8000/redoc`

### Streamlit Admin Panel

```bash
# From the project root
streamlit run streamlit_ui/app.py

# With custom port
streamlit run streamlit_ui/app.py --server.port 8501
```

The Streamlit panel connects to the FastAPI server and provides:
- Chat interface for testing conversations
- Persona editor
- QA testing panel
- Thread/session inspector

### Production Server

```bash
# Using gunicorn with uvicorn workers
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120

# Or with uvicorn directly (single worker)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Production checklist:**
- Set `ENVIRONMENT=production`
- Set `DATABASE=neon` with valid `DATABASE_URL`
- Configure `QDRANT_URL` and `QDRANT_API_KEY` for Qdrant Cloud
- Ensure all API keys are set and valid
- Set up reverse proxy (nginx) for SSL termination
- Configure health check against `/health` endpoint

---

## Testing

### Test Files

| File | Purpose |
|------|---------|
| `tests/test_api.py` | API endpoint integration tests |
| `tests/test_api_calendly.py` | Calendly API integration tests |
| `tests/test_calendly_direct.py` | Direct Calendly API tests |
| `tests/test_calendly_matching.py` | Slot matching logic tests |
| `tests/test_followup_datetime.py` | Follow-up datetime parsing tests |
| `tests/test_prompt_caching.py` | Prompt cache split logic tests |
| `tests/agent_flow_test.py` | End-to-end agent flow tests |
| `tests/comprehensive_test.py` | Comprehensive flow tests |
| `tests/single_test.py` | Single conversation test |
| `tests/verify_ingestion.py` | RAG ingestion verification |
| `tests/verify_integration.py` | Integration verification |
| `tests/_quick_validate.py` | Quick validation script |

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_api.py -v

# Run with output shown
python -m pytest tests/ -v -s

# Run quick validation
python tests/_quick_validate.py

# Run a single chat test
python tests/single_test.py
```

### Writing Tests

Test against the `/chat` endpoint for integration tests:

```python
import httpx
import asyncio

async def test_greeting():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post("/chat", json={
            "user_context": {
                "user_id": "test_user",
                "tenant_id": "test_tenant",
                "user_query": "Hello"
            }
        })
        data = response.json()
        assert response.status_code == 200
        assert data["response"]  # Non-empty response
        assert data["last_agent"] in [None, "main_agent"]
```

---

## Adding a New Agent

1. **Create agent directory:**
   ```
   app/agents/my_new_agent/
   ├── __init__.py
   └── agent.py
   ```

2. **Define the agent** in `agent.py`:
   ```python
   from agents import Agent
   from app.agents.config import get_primary_model, get_model_settings
   from app.prompts.my_new_prompt import my_prompt
   from app.core.models import BotState, MyAgentOutput
   
   def create_my_agent():
       return Agent(
           name="my_new_agent",
           instructions=lambda ctx, agent: my_prompt(ctx.context),
           model=get_primary_model(),
           model_settings=get_model_settings(),
           output_type=MyAgentOutput,  # Define in models.py
       )
   ```

3. **Export from `__init__.py`:**
   ```python
   from .agent import create_my_agent
   ```

4. **Register in `app/agents/definitions.py`:**
   ```python
   from app.agents.my_new_agent import create_my_agent
   ```

5. **Add to factory** (`app/agents/factory.py`):
   - As a **handoff**: Add to `root_agent.handoffs`
   - As a **tool**: Use `agent.as_tool(tool_name="...", tool_description="...")`

6. **Create the prompt** in `app/prompts/my_new_prompt.py`

7. **Add agent name** to `AgentName` enum in `app/config/constants.py`

---

## Adding a New Tool

Tools are plain Python functions decorated for the agent SDK:

```python
# app/tools/my_tool.py
from agents import function_tool
from app.core.models import BotState
from agents import RunContextWrapper

@function_tool
async def my_tool(ctx: RunContextWrapper[BotState], query: str) -> str:
    """Description of what this tool does — the agent reads this."""
    state = ctx.context
    # ... tool logic ...
    return "result string or JSON"
```

Register the tool on the appropriate agent in `factory.py`:
```python
agent = Agent(
    name="my_agent",
    tools=[my_tool],
    ...
)
```

---

## Adding a New Prompt

1. Create a new file in `app/prompts/`:
   ```python
   # app/prompts/my_new_prompt.py
   from app.core.models import BotState
   
   def my_prompt(state: BotState) -> str:
       persona = state.bot_persona
       return f"""You are {persona.name} from {persona.company_name}.
       
       ## Your Role
       [Instructions here]
       
       ## Current Context
       Last agent: {state.user_context.last_agent}
       """
   ```

2. Use in the agent's `instructions` parameter:
   ```python
   instructions=lambda ctx, agent: my_prompt(ctx.context)
   ```

**Prompt caching tip:** Put static content (persona definition, rules) at the TOP of the prompt and dynamic content (current state) at the BOTTOM. The `split_cached_prompt()` utility handles this automatically when `ENABLE_PROMPT_CACHING=true`.

---

## Database Migrations

### SQLite (Development)

No migrations needed — the in-memory database is created fresh on each server restart via `init_memory_db()`.

### Neon PostgreSQL (Production)

Schema changes require manual migration:

1. Update the model in `app/database/models.py`
2. Create migration SQL
3. Apply via `psql` or Neon dashboard
4. Update `get_or_create_session()` if BotState serialization changed

See [DATABASE_MIGRATIONS.md](DATABASE_MIGRATIONS.md) for detailed migration procedures.

---

## RAG Pipeline Operations

### Ingesting Documents

```python
# From code
from rag.main_runner import ingest_documents

await ingest_documents(
    tenant_id="tenant_001",
    documents=["path/to/doc.pdf", "path/to/doc2.docx"],
)
```

### Auto-Ingestion via Crawl

The `/autofill_persona` endpoint automatically:
1. Crawls the website (up to `max_pages` pages)
2. Extracts clean text content
3. Chunks and embeds the content
4. Stores in the tenant's Qdrant collection
5. Generates a `BotPersona` from the content

### Manual Qdrant Operations

```python
from rag.Qdrant.qdrant_manager import QdrantManager

manager = QdrantManager()
# List collections
collections = manager.list_collections()
# Delete a collection
manager.delete_collection("tenant_001")
```

---

## Debugging & Tracing

### Opik Tracing

When `OPIK_PROJECT_NAME` is set, all LLM calls are traced via Opik:
- View traces in the Opik dashboard
- See latency, token usage, and cost per call
- Trace full agent execution chains

### Local Debugging

1. **Enable debug mode:** Set `DEBUG=true` in `.env`
2. **Use `/chat_ui` endpoint:** Returns full `BotState` for inspection
3. **Check logs:** The application logs extensively with `[mainrunner]` and `[module_name]` prefixes
4. **Streamlit QA panel:** The admin panel has a built-in QA testing interface

### Useful Debug Queries

```bash
# Check what agent handled the last message
curl -s -X POST http://localhost:8000/chat_ui \
  -H "Content-Type: application/json" \
  -d '{"user_context": {"user_id": "debug", "user_query": "hi"}}' \
  | python -m json.tool | grep last_agent

# Check probing state
curl -s -X POST http://localhost:8000/chat_ui \
  -H "Content-Type: application/json" \
  -d '{"user_context": {"user_id": "debug", "user_query": "hello"}}' \
  | python -m json.tool | grep -A 10 probing_context

# Check guardrail decisions
curl -s ... | python -m json.tool | grep -A 5 guardrail
```

---

## Common Issues

### "No API key configured"

**Cause:** Missing `AZURE_OPENAI_KEY` or `OPENAI_API_KEY` in `.env`  
**Fix:** Ensure at least one LLM provider has valid credentials.

### "ModuleNotFoundError: agents"

**Cause:** The `openai-agents` package is not installed.  
**Fix:** `pip install openai-agents[sqlalchemy]==0.10.1` or `uv sync`

### Slow First Request

**Cause:** First request initializes models, loads settings, and warms up connections.  
**Expected:** 5–15 seconds for first request; subsequent requests are 2–8 seconds.

### "OutputGuardrailTripwireTriggered"

**Cause:** The output guardrail rejected the agent's response.  
**Expected behavior:** The system automatically uses the guardrail's `suggested_text` as a replacement. No action needed unless it's happening frequently.

### SQLite Locking in Development

**Cause:** Multiple simultaneous requests to the in-memory SQLite database.  
**Fix:** This is expected in dev. For concurrent testing, switch to `DATABASE=neon` with PostgreSQL.

### Qdrant Connection Refused

**Cause:** Qdrant server not running or incorrect URL.  
**Fix for local dev:** Run `docker run -p 6333:6333 qdrant/qdrant` or use ChromaDB fallback.

---

## Contribution Guidelines

### Code Style

- Python 3.10+ features preferred (type hints, `match/case`, etc.)
- Use `async/await` for all I/O operations
- Pydantic models for all data structures
- Type hints on all function signatures
- Docstrings on all public functions and classes

### Commit Convention

```
feat: Add new negotiation discount cap
fix: Handle null timezone in follow-up parsing
docs: Update API documentation
refactor: Extract probing engine to separate module
test: Add booking flow integration tests
```

### PR Checklist

- [ ] All existing tests pass
- [ ] New functionality has corresponding tests
- [ ] Environment variables documented if added
- [ ] Pydantic models updated if schema changed
- [ ] Prompts tested with sample conversations
- [ ] No hardcoded API keys or secrets
- [ ] Documentation updated for user-facing changes
