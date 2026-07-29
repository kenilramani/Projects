# BotRunner — Enterprise Multi-Agent Sales Bot

> **Version:** 2.0.0 &nbsp;|&nbsp; **Last Updated:** February 6, 2026 &nbsp;|&nbsp; **Built on:** [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) v0.6.1

BotRunner is a production-ready, modular multi-agent orchestration framework for intelligent sales automation, demo booking, follow-up scheduling, and human escalation workflows. It combines the power of the OpenAI Agents SDK with advanced features like RAG (Retrieval-Augmented Generation), guardrails, semantic caching, and multi-model fallback to deliver enterprise-grade conversational AI.

---

## Table of Contents

- [Key Features](#-key-features)
- [Architecture Overview](#-architecture-overview)
- [Quick Start](#-quick-start)
- [Available Agents](#-available-agents)
- [Tools & Integrations](#-tools--integrations)
- [API Endpoints](#-api-endpoints)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Key Features

### Multi-Agent Orchestration
- **7 specialized agents** (Main/Triage, Sales, Demo Booking, Follow-up, Human Escalation, Proceed-Email, Lead Analysis) with intelligent handoff routing
- **Factory pattern** with singleton caching for efficient agent creation
- **Dynamic instructions** — prompts are generated at runtime based on conversation state, persona, and context
- **Callback-driven handoffs** — state is updated via tracked callback handlers on each agent transition

### Intelligent Probing System
- **Configurable probing questions** with scoring, priority, and mandatory flags
- **Objection tracking** with configurable limits before graceful exit
- **CTA (Call-to-Action) triggers** based on accumulated probing scores vs. threshold
- **Probing question generation agent** that creates persona-aware qualifying questions

### Security & Guardrails
- **Input guardrails** — LLM-powered detection of prompt injection, jailbreak, data extraction, harmful content, and off-topic queries
- **Output guardrails** — response relevance, factual accuracy, tone alignment, and policy compliance validation
- **Safe conversational patterns** — fast bypass for greetings, acknowledgments, and fillers (no LLM call needed)
- **Structured exception hierarchy** with 15+ domain-specific exception classes

### RAG (Retrieval-Augmented Generation)
- **Dual vector database support**: ChromaDB (dev/lightweight) and Qdrant (production/scalable)
- **Semantic reranking** via Azure Cross-Encoder and Cohere Reranker
- **Multi-tenant knowledge bases** — each tenant gets an isolated collection
- **Document ingestion** — upload `.txt` files via API for per-user KB population

### Database Management
- **Alembic migrations** — version-controlled schema changes with automatic migration generation
- **Dual database support** — SQLite (development) and PostgreSQL/Neon (production)
- **Migration CLI** — convenient commands for database initialization, upgrades, and rollbacks
- **Schema tracking** — automatic revision history and state management

### Performance Optimization
- **Prompt prefix caching** — splits static/dynamic system messages for OpenAI's automatic prefix caching (50% input token savings)
- **Semantic caching** — embedding-based query matching with SentenceTransformer to skip redundant LLM calls
- **Progressive chat summarization** — turn-based summarization keeps context windows manageable
- **Executive summary generation** — milestone-triggered summaries for CRM integration

### Multi-Model Fallback
- **LiteLLM Router** with automatic failover: `GPT-4.1` → `Azure GPT-4.1` → `Gemini 3 Flash`
- **Dedicated model roles**: primary (chat), guardrail (fast validation), summarizer (summaries)
- **GPT-5 family support** with `reasoning_effort` parameter

### Enterprise Observability
- **Opik tracing** — full request, agent execution, tool call, and handoff tracing
- **Structured logging** via `logger` with DEBUG through CRITICAL levels
- **Prompt cache monitoring** — real-time hit rates, cached tokens, and cost savings metrics

### Streamlit Admin UI
- Full-featured admin panel for persona configuration, chat testing, knowledge base management, and QA evaluation

### Website Crawler & Persona Auto-Fill
- **Crawl4AI-powered** deep website crawling with BFS strategy
- Automatic extraction of company info, products, USPs, and contact details into `BotPersona`
- Simultaneous knowledge base ingestion of crawled content

---

## 🏗 Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                            │
│  /chat  /chat_ui  /generate_probing_questions  /autofill_persona     │
│  /ingest_documents  /generate_instructions  /health  /cache_stats    │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     Application Layer                                 │
│  app_agent.py → Session Init → Cache Lookup → Agent Execution        │
│              → State Finalization → Summarization → DB Save           │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Agent System                                   │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────┐    │
│   │              Root Agent (main_agent / Triage)                │    │
│   │   Routes to specialized agents via handoffs + callbacks      │    │
│   └──────┬──────┬──────────┬───────────┬──────────┬─────────────┘    │
│          │      │          │           │          │                    │
│          ▼      ▼          ▼           ▼          ▼                    │
│   ┌──────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐          │
│   │Sales │ │Demo    │ │Follow  │ │Human   │ │Proceed     │          │
│   │Agent │ │Booking │ │-up     │ │Agent   │ │Email Agent │          │
│   └──────┘ │Agent   │ │Agent   │ └────────┘ └────────────┘          │
│            └───┬────┘ └────────┘                                      │
│                │                                                       │
│                ▼                                                       │
│         ┌─────────────┐                                               │
│         │Lead Analysis│  (used as tool by Demo Booking Agent)         │
│         │Agent        │                                               │
│         └─────────────┘                                               │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Tools & Integrations                                │
│  retrieve_query │ process_booking_datetime │ check_calendly           │
│  get_timezone   │ process_followup_datetime│ validate_email           │
│  lead_analysis_tool │ proceed_with_email (agent-as-tool)             │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Data Layer                                     │
│  SQLite/Neon PostgreSQL │ ChromaDB/Qdrant │ Semantic Cache (in-mem)   │
└──────────────────────────────────────────────────────────────────────┘
```

> 📖 For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **OpenAI API Key** (required)
- **Azure OpenAI Key** (optional — for fallback)
- **Gemini API Key** (optional — for fallback)

### 1. Clone & Install

```bash
git clone <repository-url>
cd botrunner

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env_example .env
# Edit .env with your API keys and configuration
```

**Minimum required settings:**
```env
OPENAI_API_KEY=sk-your-key-here
DATABASE=SQLite
VECTORDB=chromadb
PRIMARY_MODEL=gpt-4.1
GUARDRAIL_MODEL=gpt-4o-mini
SUMMARIZER_MODEL=gpt-5-nano
```

### 3. Initialize Database

```bash
# Run database migrations (creates session_state table)
python scripts/migrate.py init

# Verify database setup
python scripts/migrate.py current
```

> 📖 For database migration details, see [docs/DATABASE_MIGRATIONS.md](docs/DATABASE_MIGRATIONS.md) or [ALEMBIC_QUICKREF.md](ALEMBIC_QUICKREF.md).

### 4. Run the Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Test the API

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_context": {
      "user_id": "user_001",
      "user_query": "Tell me about your products"
    },
    "bot_persona": {
      "name": "Arya",
      "company_name": "AI Sante",
      "company_description": "AI-powered sales automation",
      "company_products": [
        {"id": "p1", "name": "AI Sales Bot", "description": "Automated sales conversations"}
      ]
    }
  }'
```

---

## 🤖 Available Agents

| Agent | Name Constant | Purpose | Key Tools |
|-------|--------------|---------|-----------|
| **Main (Triage)** | `main_agent` | Routes conversations to specialized agents based on user intent | `proceed_with_email` (agent-as-tool) |
| **Sales** | `sales_agent` | Handles product inquiries, pricing, features, and company info | `retrieve_query` (RAG) |
| **Demo Booking** | `demo_booking_agent` | Manages new bookings, rescheduling, and cancellations with Calendly | `get_timezone`, `process_booking_datetime`, `check_calendly_availability`, `lead_analysis_tool` |
| **Follow-up** | `followup_agent` | Schedules future interactions ("remind me tomorrow", "ping me in 5 min") | `get_timezone`, `process_followup_datetime` |
| **Human** | `human_agent` | Handles escalation to human support with conversation summarization | `validate_email` |
| **Proceed Email** | `switch_to_email_agent` | Manages transition from chat to email communication | — |
| **Lead Analysis** | `lead_analysis_agent` | Classifies leads as hot/warm/cold after successful bookings | — |

**Standalone Agents** (not part of main agent graph):

| Agent | Purpose |
|-------|---------|
| **Probing Agent** | Generates persona-aware qualifying questions |
| **Probing Instruction Agent** | Generates instruction suggestions for probing question creation |
| **Crawl Persona Agent** | Crawls websites and auto-fills `BotPersona` from extracted content |

---

## 🔧 Tools & Integrations

| Tool | Module | Used By | Description |
|------|--------|---------|-------------|
| `retrieve_query` | `app/tools/sales_tools.py` | Sales Agent | RAG query against ChromaDB/Qdrant knowledge base |
| `process_booking_datetime` | `app/tools/booking_tools.py` | Demo Booking Agent | Unified datetime parsing, validation, and UTC conversion |
| `check_calendly_availability` | `app/tools/booking_tools.py` | Demo Booking Agent | Checks Calendly for available meeting slots |
| `get_timezone` | `app/tools/followup_timezone.py` | Demo Booking, Follow-up | Resolves region code to IANA timezone(s) |
| `process_followup_datetime` | `app/tools/followup_timezone.py` | Follow-up Agent | Parses, validates, and converts follow-up time expressions |
| `validate_email` | `app/tools/human_tools.py` | Human Agent | Email format validation with typo detection and correction |
| `lead_analysis_tool` | Agent-as-tool | Demo Booking Agent | Classifies lead quality post-booking (hot/warm/cold) |
| `proceed_with_email` | Agent-as-tool | Main Agent | Triggers email communication flow |

> 📖 For complete tool reference, see [docs/TOOLS_REFERENCE.md](docs/TOOLS_REFERENCE.md).

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Main chat endpoint — returns `APIResponse` with response text and metadata |
| `POST` | `/chat_ui` | Streamlit UI endpoint — returns full `BotState` as dictionary |
| `POST` | `/generate_probing_questions` | Generate probing questions from persona |
| `POST` | `/generate_instructions` | Generate instruction suggestions for probing |
| `POST` | `/autofill_persona` | Crawl a website and auto-generate `BotPersona` |
| `POST` | `/ingest_documents` | Upload `.txt` file to populate per-user knowledge base |
| `GET`  | `/health` | Health check |
| `GET`  | `/cache_stats` | Prompt cache performance statistics |
| `POST` | `/cache_stats/reset` | Reset prompt cache statistics |

> 📖 For complete API documentation, see [docs/API.md](docs/API.md).

---

## ⚙️ Configuration

### Environment Variables

Configuration is managed via `.env` file and Pydantic `BaseSettings` in `app/config/settings.py`.

| Category | Variable | Default | Description |
|----------|----------|---------|-------------|
| **Environment** | `ENVIRONMENT` | `development` | `development`, `staging`, `production` |
| **Database** | `DATABASE` | `SQLite` | `SQLite` or `neon` (PostgreSQL) |
| **Vector DB** | `VECTORDB` | `chromadb` | `chromadb` or `qdrant` |
| **Models** | `PRIMARY_MODEL` | `gpt-4.1` | Primary conversational model |
| | `GUARDRAIL_MODEL` | `gpt-4o-mini` | Fast model for guardrail checks |
| | `SUMMARIZER_MODEL` | `gpt-5-nano` | Model for summarization tasks |
| | `AZURE_FALLBACK_MODEL` | `azure/gpt-4.1` | Azure fallback |
| | `GEMINI_FALLBACK_MODEL` | `gemini/gemini-3-flash-preview` | Gemini fallback |
| **Caching** | `ENABLE_PROMPT_CACHING` | `true` | Enable prompt prefix caching |
| **Summarizer** | `SUMMRIZE_CONTEXT_LENGTH` | `3` | Turns before triggering summarization |
| | `SUMMRIZE_KEEP_LAST_N_TURNS` | `3` | Recent turns to keep verbatim |
| **History** | `MAX_HISTORY` | `15` | Max chat history messages |
| **Observability** | `OPIK_PROJECT_NAME` | — | Opik project name for tracing |

> See [.env_example](.env_example) for the complete list of all supported environment variables.

---

## 💡 Usage Examples

### Python Client

```python
import httpx
import asyncio

async def chat():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/chat",
            json={
                "user_context": {
                    "user_id": "user_123",
                    "user_query": "I'd like to book a demo for next Tuesday at 3 PM"
                },
                "bot_persona": {
                    "name": "Arya",
                    "company_name": "AI Sante",
                    "enable_probing": True,
                    "probing_threshold": 50
                }
            }
        )
        data = response.json()
        print(f"Bot: {data['response']}")

asyncio.run(chat())
```

### Generate Probing Questions

```python
response = await client.post(
    "http://localhost:8000/generate_probing_questions",
    json={
        "custom_persona": {
            "company_name": "AI Sante",
            "industry": "IT",
            "business_type": "Seller"
        },
        "total_k": 5,
        "comment": "Focus on budget and timeline"
    }
)
```

### Auto-Fill Persona from Website

```python
response = await client.post(
    "http://localhost:8000/autofill_persona",
    json={
        "user_id": "tenant_001",
        "url": "https://example.com",
        "max_depth": 2,
        "max_pages": 50
    }
)
persona = response.json()["bot_persona"]
```

---

## 📁 Project Structure

```
botrunner/
├── main.py                      # FastAPI server entry point
├── app_agent.py                 # Chatbot execution engine
├── requirements.txt             # Python dependencies
├── .env_example                 # Environment variable template
│
├── app/                         # Core application
│   ├── agents/                  # Agent definitions & factory (modern architecture)
│   │   ├── base.py              # Abstract base classes & protocols
│   │   ├── definitions.py       # All agent creator functions
│   │   └── factory.py           # AgentFactory with singleton caching
│   ├── agent/                   # Standalone agents
│   │   ├── crawl_persona_agent.py  # Website crawler + persona generation
│   │   ├── probing_agent.py     # Probing question generation
│   │   ├── probing_instruction_agent.py  # Instruction generation
│   │   └── my_agents.py         # Legacy agent definitions
│   ├── apis/                    # External API integrations
│   │   └── calendly_api.py      # Calendly scheduling API
│   ├── callbacks/               # Handoff callback handlers
│   │   └── handlers.py          # on_sales_handoff, on_demo_handoff, etc.
│   ├── config/                  # Configuration management
│   │   ├── settings.py          # Pydantic BaseSettings (env-based)
│   │   └── constants.py         # Enums and constants
│   ├── core/                    # Core business logic
│   │   ├── models.py            # 20+ Pydantic v2 data models
│   │   ├── exceptions.py        # 15+ custom exception classes
│   │   ├── guardrail.py         # Input/output guardrails
│   │   ├── probing.py           # ProbingEngine for score tracking
│   │   ├── request_context.py   # Thread-safe request context
│   │   └── state.py             # Backward-compatible re-exports
│   ├── database/                # Persistence layer
│   │   ├── session_manager.py   # SQLite/Neon session management
│   │   ├── cachememory.py       # Semantic similarity caching
│   │   ├── summarizer.py        # Progressive conversation summarization
│   │   └── executive_summary.py # Milestone-triggered executive summaries
│   ├── instructions/            # Dynamic instruction generation
│   │   └── generators.py        # InstructionBuilder pattern
│   ├── prompts/                 # Prompt templates (18 modules)
│   ├── route/                   # LLM routing layer
│   │   └── route.py             # LiteLLM Router + RouterModel
│   ├── tools/                   # Agent-callable tools
│   │   ├── sales_tools.py       # retrieve_query (RAG)
│   │   ├── booking_tools.py     # Datetime processing + Calendly
│   │   ├── followup_timezone.py # Timezone + follow-up datetime
│   │   └── human_tools.py       # Email validation
│   └── utils/                   # Shared utilities
│       ├── prompt_cache.py      # Prompt caching monitor
│       └── utils.py             # General utilities
│
├── rag/                         # RAG pipeline
│   ├── chroma_db/               # ChromaDB vector store + ETL
│   └── qdrant_db/               # Qdrant vector store + ETL
│
├── streamlit_ui/                # Streamlit admin UI
├── data/                        # SQLite database storage
├── docs/                        # Documentation
├── tests/                       # Test suite
└── evals/                       # Evaluation datasets
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, components, design patterns, data models |
| [DEVELOPERS.md](docs/DEVELOPERS.md) | Developer guide: setup, workflows, API reference, debugging |
| [DATABASE_MIGRATIONS.md](docs/DATABASE_MIGRATIONS.md) | Database migration guide with Alembic: setup, commands, workflows |
| [AGENT_FLOWS.md](docs/AGENT_FLOWS.md) | Detailed per-agent interaction flows and multi-agent workflows |
| [TOOLS_REFERENCE.md](docs/TOOLS_REFERENCE.md) | Complete tools inventory with parameters, outputs, and examples |
| [PRODUCT_FEATURES.md](docs/PRODUCT_FEATURES.md) | Feature catalog with technical details and configuration |
| [QA.md](docs/QA.md) | Testing strategy, test cases, quality metrics |
| [PM.md](docs/PM.md) | Product management guide: vision, roadmap, user stories |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment guide: infrastructure, monitoring, security |
| [API.md](docs/API.md) | API endpoint documentation |
| [CHANGELOG.md](docs/CHANGELOG.md) | Version history |
| [POETRY.md](POETRY.md) | Poetry package management guide |
| [PUBLISHING.md](docs/PUBLISHING.md) | Complete guide to building and publishing pip packages |
| [ALEMBIC_QUICKREF.md](ALEMBIC_QUICKREF.md) | Quick reference for database migrations |

---

## 🧪 Testing

```bash
# Run quick validation
python tests/_quick_validate.py

# Run comprehensive tests
python tests/comprehensive_test.py

# Run specific tests
python tests/test_api.py
python tests/test_followup_datetime.py
python tests/test_prompt_caching.py
python tests/test_calendly_matching.py
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-feature`
3. **Follow** code conventions: Pydantic v2 models, `@function_tool` decorator, `logger` logging
4. **Write** tests for new features
5. **Update** documentation for any changes
6. **Submit** a pull request with a clear description

> 📖 See [docs/DEVELOPERS.md](docs/DEVELOPERS.md) for detailed contributing guidelines.

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 📞 Contact

For questions, bug reports, or feature requests, please contact the development team or open an issue in the repository.

