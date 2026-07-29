# BotRunner System Architecture

> **Last Updated:** March 6, 2026 &nbsp;|&nbsp; **Version:** 2.1.0  
> **Audience:** Developers, Architects, DevOps Engineers

---

## Table of Contents

- [High-Level Overview](#high-level-overview)
- [System Architecture Diagram](#system-architecture-diagram)
- [Core Components](#core-components)
  - [1. API Layer (FastAPI)](#1-api-layer-fastapi)
  - [2. Execution Pipeline (app_agent.py)](#2-execution-pipeline-app_agentpy)
  - [3. Agent Orchestration Layer](#3-agent-orchestration-layer)
  - [4. LLM Router (LiteLLM)](#4-llm-router-litellm)
  - [5. Data Layer](#5-data-layer)
  - [6. RAG Pipeline](#6-rag-pipeline)
  - [7. Guardrail System](#7-guardrail-system)
  - [8. Prompt System](#8-prompt-system)
- [Data Flow](#data-flow)
  - [Request Lifecycle](#request-lifecycle)
  - [State Management Flow](#state-management-flow)
- [Third-Party Integrations](#third-party-integrations)
- [Deployment Topology](#deployment-topology)
- [Design Patterns](#design-patterns)
- [Module Dependency Map](#module-dependency-map)

---

## High-Level Overview

BotRunner is a **multi-agent conversational AI platform** for sales automation. It orchestrates multiple specialized AI agents to handle product inquiries, demo booking, pricing negotiation, follow-ups, and human escalation — all within a single conversation.

**Key architectural decisions:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent framework | OpenAI Agents SDK v0.10.1 | Native handoff, tools, guardrails, structured output |
| LLM routing | LiteLLM v1.80.11 + Router | Multi-provider fallback (Azure → OpenAI → Gemini) |
| API framework | FastAPI | Async-native, auto-generated docs, Pydantic integration |
| State management | Pydantic models + session persistence | Type-safe, serializable, validatable |
| Vector database | Qdrant (prod) / ChromaDB (dev) | Production-grade vector search with tenant isolation |
| Observability | Opik v1.9.69 | LLM-specific tracing and cost tracking |
| Relational DB | SQLite (dev) / Neon PostgreSQL (prod) | Zero-config dev, managed Postgres for production |

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│   Streamlit UI (/chat_ui)  │  API Clients (/chat)  │  Webhooks      │
└───────────────┬───────────────────────┬──────────────────────────────┘
                │                       │
                ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FASTAPI SERVER (main.py)                       │
│                                                                      │
│  /health  /chat  /chat_ui  /autofill_persona  /generate_*           │
│  /cache_stats  /generate_executive_summary  /generate_templates     │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   EXECUTION PIPELINE (app_agent.py)                  │
│                                                                      │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌────────┐  ┌──────────┐  │
│  │ Session  │→ │ Semantic │→ │ Agent  │→ │ State  │→ │ Persist  │  │
│  │ Load     │  │ Cache    │  │ Run    │  │ Final. │  │ & Return │  │
│  └─────────┘  └──────────┘  └────────┘  └────────┘  └──────────┘  │
│       │                          │                                   │
│       ▼                          ▼                                   │
│  ┌─────────┐           ┌─────────────────┐                          │
│  │ Probing │           │  Negotiation    │                          │
│  │ Engine  │           │  Engine         │                          │
│  │ State   │           │  (protected $)  │                          │
│  └─────────┘           └─────────────────┘                          │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   AGENT ORCHESTRATION LAYER                          │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │                    ROOT AGENT (main_agent)                  │     │
│  │  Input Guardrail → Intent Classification → Route            │     │
│  └─────┬──────────┬──────────┬──────────┬──────────────────────┘     │
│        │          │          │          │                             │
│   ┌────▼────┐ ┌──▼───┐ ┌───▼────┐ ┌──▼─────┐                      │
│   │  Sales  │ │ Demo │ │Followup│ │ Human  │  ← Handoff Agents     │
│   │  Agent  │ │Booking│ │ Agent  │ │ Agent  │                       │
│   └────┬────┘ └──┬───┘ └───┬────┘ └────────┘                       │
│        │         │         │                                         │
│   ┌────▼────┐ ┌──▼─────┐ ┌▼────────┐                               │
│   │Objection│ │  Lead  │ │Timezone │  ← Tool Agents                 │
│   │Handler  │ │Analysis│ │Resolver │                                │
│   └─────────┘ └────────┘ └─────────┘                                │
│                                                                      │
│   Tools on Root Agent:                                               │
│   ┌──────────┐ ┌───────────┐ ┌─────────────┐                       │
│   │Negotiate │ │  Email    │ │  Asset      │                        │
│   │Engine    │ │  Switch   │ │  Sharing    │                        │
│   └──────────┘ └───────────┘ └─────────────┘                        │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
┌──────────────────┐ ┌───────────┐ ┌───────────────┐
│   LLM ROUTER     │ │  DATA     │ │  RAG          │
│   (LiteLLM)      │ │  LAYER    │ │  PIPELINE     │
│                   │ │           │ │               │
│  Azure GPT-5.1   │ │ SQLite/   │ │ Qdrant /      │
│    ↓ fallback     │ │ Neon PG   │ │ ChromaDB      │
│  OpenAI GPT-5.1  │ │           │ │               │
│    ↓ fallback     │ │ Semantic  │ │ FastEmbed     │
│  Gemini 3 Flash  │ │ Cache     │ │ + Reranker    │
└──────────────────┘ └───────────┘ └───────────────┘
```

---

## Core Components

### 1. API Layer (FastAPI)

**File:** `main.py` (332 lines)

The API layer exposes 10 HTTP endpoints via FastAPI. It handles request validation (Pydantic), routing to internal functions, and response serialization.

| Endpoint | Handler | Internal Function |
|----------|---------|-------------------|
| `GET /health` | `health_check()` | Direct response |
| `POST /chat` | `chat_endpoint()` | `run_chatbot_api()` |
| `POST /chat_ui` | `chat_streamlit()` | `run_chatbot_api()` |
| `POST /generate_executive_summary` | `generate_executive_summary_endpoint()` | `generate_executive_summary()` |
| `POST /generate_probing_questions` | `generate_probing_questions()` | `run_probing_agent()` |
| `POST /autofill_persona` | `autofill_persona()` | `run_crawl_persona_agent()` |
| `POST /generate_instructions` | `generate_probing_instructions_endpoint()` | `generate_probing_question_instructions()` |
| `POST /generate_templates` | `generate_templates_endpoint()` | `run_template_generation_agent()` |
| `GET /cache_stats` | `get_cache_stats()` | `cache_monitor.get_stats()` |
| `POST /cache_stats/reset` | `reset_cache_stats()` | `cache_monitor.reset()` |

**Startup:** Initializes the in-memory SQLite database via `init_memory_db()`.

**Error strategy:** The `/chat` endpoint catches all exceptions and returns a friendly fallback response (200 OK). All other endpoints propagate errors as HTTP 500.

---

### 2. Execution Pipeline (app_agent.py)

**File:** `app_agent.py` (1131 lines)

The central execution pipeline that processes every chat message. Implements a 10-step processing flow:

```
1. Session Load
   └→ get_or_create_session(user_id) → BotState
   └→ Merge incoming request with existing state

2. State Initialization
   └→ ProbingEngineState.from_state(state)
   └→ NegotiationEngine.from_state(state)
   └→ Generate message_id (UUID v4) if not provided

3. Semantic Cache Check
   └→ retrieve_from_cache(user_id, query)
   └→ If hit (similarity > 0.5): skip agent execution, return cached

4. Agent Execution
   └→ Runner.run(root_agent, input, context=RunContextWrapper(state))
   └→ RunConfig with SQLiteSession for agent-level persistence
   └→ Handles OutputGuardrailTripwireTriggered → uses suggested_text

5. Response Extraction
   └→ Parse BotResponse from agent output (JSON)
   └→ Extract: response text, CTA flags, booking fields, email details

6. Probing State Sync
   └→ ProbingEngineState.apply_to_state(state, probing_output)
   └→ Score updates, question tracking, objection handling

7. Negotiation State Sync
   └→ NegotiationEngine.apply_to_state(state, negotiation_response)
   └→ Protected field enforcement, discount validation

8. History Management
   └→ Append user/assistant turns to chat_history
   └→ Sliding window: keep last MAX_HISTORY (15) messages
   └→ Summarize older messages if to_summarise=True

9. Executive Summary
   └→ Generate on every turn (async via summarizer model)
   └→ Stored in state.user_context.executive_summary

10. State Persistence
    └→ save_state(user_id, state) → SQLite/PostgreSQL
    └→ update_session(user_id, query, response) → Semantic cache
    └→ Return BotState
```

**Key classes used:**
- `ProbingEngineState` — manages probing score, question tracking, objection counts
- `NegotiationEngine` — manages pricing, discounts, protected fields
- `Runner` (from OpenAI Agents SDK) — executes the agent graph
- `RunContextWrapper` — passes `BotState` as context through the agent execution

---

### 3. Agent Orchestration Layer

**Factory:** `app/agents/factory.py` (438 lines) — `AgentFactory` class

The agent system uses the **OpenAI Agents SDK** orchestration pattern:

```python
# Simplified structure
root_agent = Agent(
    name="main_agent",
    instructions=dynamic_main_instructions,  # context-aware prompt
    handoffs=[sales_agent, demo_booking_agent, followup_agent, human_agent],
    tools=[proceed_with_email, negotiation_engine, proceed_with_asset_sharing],
    input_guardrails=[input_attack],
    output_type=BotResponse,
)
```

**Agent types:**

| Type | SDK Feature | Control Flow |
|------|-------------|--------------|
| Handoff Agent | `Agent()` with `handoff()` | Root transfers full control; child runs independently |
| Tool Agent | `agent.as_tool()` | Root retains control; tool returns structured output inline |
| Standalone Agent | `Agent()` run directly | Called by API endpoints without root agent involvement |

**Handoff callbacks** (`app/callbacks/handlers.py`):
- `on_sales_handoff`: Sets `new_booking=True`, detects language/script
- `on_demo_handoff`: Sets `new_booking=True`, detects language/script
- `on_followup_handoff`: Sets `follow_trigger=True`
- `on_human_handoff`: Sets `human_requested=True`, `escalation_timestamp`, `last_agent="human_agent"`

---

### 4. LLM Router (LiteLLM)

**File:** `app/route/route.py` (304 lines)

Implements a **multi-provider LLM router** with role-based fallback chains.

#### Model Roles

| Role | Primary (Azure) | Fallback 1 (OpenAI) | Fallback 2 (Gemini) |
|------|-----------------|---------------------|---------------------|
| `primary` | `azure/gpt-5.1-chat` | `gpt-5.1-chat-latest` | `gemini/gemini-3-flash-preview` |
| `guardrail` | `azure/gpt-4.1-nano` | `gpt-4.1-nano` | `gemini/gemini-3-flash-preview` |
| `summarizer` | `azure/gpt-4.1-nano` | `gpt-4.1-nano` | `gemini/gemini-3-flash-preview` |

#### RouterModel Class

```python
class RouterModel(LitellmModel):
    """Custom model class that routes through the global litellm.Router."""
```

Key features:
- Extends `LitellmModel` from the OpenAI Agents SDK LiteLLM extension
- Overrides `_fetch_response()` to route through the LiteLLM Router
- **GPT-5 detection:** Sets `reasoning_effort="medium"` for GPT-5 family models
- **Prompt caching:** Splits system instructions into `developer` (static) and `developer` (dynamic) messages for optimal OpenAI prompt prefix caching
- **Token tracking:** Captures `usage` from LLM response and feeds into `ConsumptionInfo`
- **Opik integration:** LLM calls are traced via `track_completion()` patch

#### Router Configuration

```python
LITELLM_SETTINGS = {
    "num_retries": 0,       # No retries within same provider
    "timeout": 30,          # 30-second timeout per call
}

# Allowed errors that trigger fallback
litellm.allowed_fallback_errors = [
    "rate_limit", "timeout", "internal_server_error",
    "context_length_exceeded", "authentication_error", ...
]
```

---

### 5. Data Layer

#### Session Storage

| Component | Dev | Production |
|-----------|-----|------------|
| Session DB | SQLite (in-memory) | Neon PostgreSQL (async) |
| Agent Session | SQLiteSession (SDK built-in) | SQLiteSession |
| ORM | SQLAlchemy async | SQLAlchemy async + asyncpg |

**Session Manager** (`app/database/session_manager.py`):
- `init_memory_db()` — Creates in-memory SQLite tables at startup
- `get_or_create_session(user_id)` → `BotState`
- `save_state(user_id, state)` → persist to DB
- BotState serialized as JSON in a single column

**PostgreSQL Manager** (`app/database/postgresql_session_manager.py`):
- Async via `asyncpg` + SQLAlchemy async engine
- Used when `DATABASE=neon`
- Connection pooling via SQLAlchemy

#### Semantic Cache

**File:** `app/database/cachememory.py`

- Per-user embedding cache for query deduplication
- Max 15 entries per user (FIFO eviction)
- Similarity threshold: cosine > 0.5
- Embeddings: Azure OpenAI embedding model
- On cache hit: returns stored response without LLM execution

#### Conversation Summarizer

**File:** `app/database/summarizer.py`

- Summarizes older conversation turns when window exceeds threshold
- Uses `summarizer` model role (gpt-4.1-nano)
- Maintains `chat_summary` in state for context continuity

#### Sliding Window

**File:** `app/database/sliding_window.py`

- Keeps last `MAX_HISTORY` (default: 15) messages in `chat_history`
- Older messages are summarized and compressed into `chat_summary`

---

### 6. RAG Pipeline

**Directory:** `rag/`

```
rag/
├── main_runner.py          # Entry point for RAG operations
├── Qdrant_initializer.py   # Collection initialization
├── config/                 # RAG-specific config
├── ETL_Pipeline/           # Document ingestion pipeline
│   ├── ingestion.py        # Main ingestion orchestrator
│   ├── docling.py          # PDF/DOCX processing via Docling
│   └── ...
├── Qdrant/                 # Vector DB operations
│   ├── qdrant_manager.py   # CRUD operations
│   └── ...
└── retriever/              # Search and retrieval
    ├── base_retriever.py   # Base retrieval class
    ├── hybrid_search.py    # Hybrid search implementation
    └── reranker.py         # Cross-encoder reranking
```

**Flow:**
1. **Ingestion:** Documents → Docling (PDF/DOCX parsing) → Text chunking (LangChain splitters) → Embeddings (FastEmbed) → Qdrant collections
2. **Retrieval:** User query → Embedding → Qdrant hybrid search → Cross-encoder reranking → Top-K results
3. **Tenant isolation:** Each tenant gets a separate Qdrant collection (`collection_name = tenant_id`)

**Used by:**
- `sales_agent` → `retrieve_query` tool for knowledge base lookups
- `/autofill_persona` endpoint → auto-ingests crawled website content into KB

---

### 7. Guardrail System

**File:** `app/core/guardrail.py` (547 lines)

Two-layer guardrail system protecting input and output:

```
                    Input Guardrail                    Output Guardrail
                    ┌────────────┐                     ┌────────────┐
User Message ──────►│ Fast-path  │                     │ 12 rules   │
                    │ (regex)    │──match──► SAFE       │ validation │
                    │            │                     │            │
                    │ LLM guard  │──classify──► RECORD │ approved?  │──no──► Use suggested_text
                    │ (nano)     │   (never blocks)    │ (nano)     │──yes─► Pass through
                    └────────────┘                     └────────────┘
```

**Input guardrail:**
- `SAFE_CONVERSATIONAL_PATTERNS`: 50+ regex patterns for greetings, acknowledgments, fillers
- Fast-path: No LLM call for matching patterns → classification `"safe"`
- LLM path: Classifies as `safe/prompt_injection/jailbreak/data_extraction/harmful_content/off_topic`
- **Record-only** — `tripwire_triggered` is always `False`

**Output guardrail:**
- 12 validation rules (domain scope, accuracy, tone, privacy, etc.)
- **Active** — can reject responses (`validation_status_approved="no"`)
- On trip: `OutputGuardrailTripwireTriggered` exception → `suggested_text` used as replacement
- On guardrail error: fail-open (original response passes through)

---

### 8. Prompt System

**Directory:** `app/prompts/`

All prompts are functions that accept `BotState` (via `RunContextWrapper`) and return dynamically generated instruction text.

| Prompt File | Agent | Key Context Injected |
|-------------|-------|---------------------|
| `instruction.py` (870 lines) | Main agent | Full persona, products, rules, probing state, CTA, collected fields |
| `dynamic_sales.py` | Sales agent | Persona personality, products, KB context |
| `demo_booking.py` (1162 lines) | Demo booking | Working hours, Calendly config, collected fields, products |
| `followup.py` | Follow-up agent | Timezone, existing follow-up state |
| `human_agent.py` | Human escalation | Conversation summary, contact details |
| `negotiation.py` | Negotiation engine | Products with pricing, discount config, negotiation history |
| `asset_sharing.py` | Asset sharing | Available assets list |
| `proceed_with_email.py` | Email switch | Email templates, contact details |
| `input_guardrail.py` | Input guardrail | Classification categories |
| `generate_probing_question.py` | Probing agent | Persona, existing questions |
| `generate_probing_instructions.py` | Instruction agent | Persona context |

**Prompt caching strategy** (when `ENABLE_PROMPT_CACHING=true`):
- System instructions are split into **static** (persona definition, rules) and **dynamic** (current state, conversation context) parts
- Static parts are sent as the first `developer` message → maximizes OpenAI's automatic prompt prefix caching
- Dynamic parts follow as a second `developer` message
- Split logic in `app/utils/prompt_cache.py` → `split_cached_prompt()`

---

## Data Flow

### Request Lifecycle

```
1. HTTP Request (BotRequest JSON)
   │
   ▼
2. FastAPI validates via Pydantic
   │
   ▼
3. convert_to_botstate(request) → BotState
   │ Merges: incoming UserContextRequest + stored session state + BotPersona
   │
   ▼
4. run_chatbot_api(state) ─── [10-step pipeline in app_agent.py]
   │
   ├─ 4a. Load/create session
   ├─ 4b. Initialize probing + negotiation engines
   ├─ 4c. Check semantic cache → HIT? Return cached
   ├─ 4d. Execute agent graph (Runner.run)
   │      │
   │      ├── Input guardrail (async, record-only)
   │      ├── Main agent processes intent
   │      ├── Handoff or tool call (if needed)
   │      ├── Child agent/tool executes
   │      ├── Output guardrail (async, can block)
   │      └── Return BotResponse
   │
   ├─ 4e. Sync probing state
   ├─ 4f. Sync negotiation state
   ├─ 4g. Update chat_history (sliding window)
   ├─ 4h. Generate executive summary
   ├─ 4i. Persist state + update semantic cache
   └─ 4j. Return updated BotState
   │
   ▼
5. Map BotState → APIResponse (for /chat) or full dict (for /chat_ui)
   │
   ▼
6. HTTP Response (JSON)
```

### State Management Flow

```
BotState (central state object)
├── user_context: UserContext
│   ├── user_id, tenant_id, user_query
│   ├── chat_history[], chat_summary
│   ├── collected_fields (booking data)
│   ├── contact_details (name, email, phone)
│   ├── follow_trigger, booking_confirmed, last_agent
│   └── ... (40+ fields)
│
├── bot_persona: BotPersona
│   ├── name, company_name, industry
│   ├── products[], assets[], email_template[]
│   ├── working_hours[], rules[]
│   ├── probing config (questions, threshold, CTA)
│   ├── negotiation_config
│   └── ... (30+ fields)
│
├── probing_context: ProbingContext
│   ├── total_score, probing_completed
│   ├── detected_question_answer[]
│   └── can_show_cta
│
├── objection_state: ObjectionState
│   ├── current_objection_count
│   ├── is_objection_limit_reached
│   └── limit_reach_count
│
├── negotiation_state: NegotiationState
│   ├── negotiation_session (products, discounts)
│   └── negotiation_attempts
│
├── response: str (bot's reply text)
├── input_guardrail_decision: InputGuardrail
└── brochure_flag, brochure_details, human_requested, ...
```

State is **mutable** — agents modify it through the `RunContextWrapper` during execution. After agent execution, the pipeline syncs probing/negotiation changes back into the state object.

---

## Third-Party Integrations

| Service | Library | Purpose | Configuration |
|---------|---------|---------|---------------|
| **Azure OpenAI** | `litellm` | Primary LLM (GPT-5.1-chat, GPT-4.1-nano) | `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT` |
| **OpenAI** | `litellm` | Fallback LLM | `OPENAI_API_KEY` |
| **Google Gemini** | `litellm` | Final fallback LLM | `GEMINI_API_KEY` |
| **Qdrant** | `qdrant-client` | Production vector database | `QDRANT_URL`, `QDRANT_API_KEY` |
| **Neon PostgreSQL** | `asyncpg` + SQLAlchemy | Production session storage | `DATABASE_URL`, `DATABASE=neon` |
| **Calendly** | `httpx` (REST API) | Demo slot availability checking | Configured in booking tools |
| **Opik** | `opik` | LLM observability and tracing | `OPIK_PROJECT_NAME`, `OPIK_WORKSPACE` |
| **Crawl4AI** | `crawl4ai` | Website crawling for persona autofill | Used in `/autofill_persona` endpoint |
| **Azure Blob Storage** | `azure-storage-blob` | Document storage for RAG pipeline | Azure credentials |
| **Azure AI Document Intelligence** | `azure-ai-documentintelligence` | PDF/document parsing | Azure credentials |
| **Cohere** | `cohere` (REST) | Reranker for RAG retrieval | `COHERE_RERANKER_API_KEY` |
| **FastEmbed** | `fastembed` | Local embedding generation for RAG | No external API needed |

---

## Deployment Topology

### Development

```
┌─────────────────────────────────────┐
│           Local Machine              │
│                                      │
│  uvicorn main:app --reload           │
│     ├── SQLite (in-memory)           │
│     ├── ChromaDB (local)             │
│     └── Azure/OpenAI API calls       │
│                                      │
│  streamlit run streamlit_ui/app.py   │
│     └── Connects to localhost:8000   │
└─────────────────────────────────────┘
```

### Production

```
┌────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Load Balancer │────►│  App Server(s)   │────►│  Neon PostgreSQL│
│  (nginx/ALB)   │     │  uvicorn + gunicorn│    │  (sessions)     │
└────────────────┘     │  main:app         │     └─────────────────┘
                       │                    │
                       │  ┌──────────────┐  │     ┌─────────────────┐
                       │  │ LiteLLM      │──┼────►│  Azure OpenAI   │
                       │  │ Router       │  │     │  (LLM calls)    │
                       │  └──────────────┘  │     └─────────────────┘
                       │                    │
                       │  ┌──────────────┐  │     ┌─────────────────┐
                       │  │ RAG Pipeline │──┼────►│  Qdrant Cloud   │
                       │  └──────────────┘  │     │  (vector search) │
                       └────────────────────┘     └─────────────────┘
```

### Environment Toggle

| Setting | Dev Value | Prod Value |
|---------|-----------|------------|
| `DATABASE` | `SQLite` | `neon` |
| `DATABASE_URL` | N/A (in-memory) | `postgresql+asyncpg://...` |
| `QDRANT_URL` | `localhost:6333` | `https://xxx.qdrant.io` |
| `ENVIRONMENT` | `development` | `production` |

---

## Design Patterns

### 1. Agent-as-Tool Pattern

Specialized agents are wrapped as tools on the root agent using the SDK's `agent.as_tool()` method. This allows the root agent to call them inline without losing control:

```python
negotiation_engine = negotiation_engine_agent.as_tool(
    tool_name="negotiation_engine",
    tool_description="Handle pricing and discount inquiries",
)
```

### 2. Handoff with Callbacks

Agent handoffs use callbacks to mutate state at the moment of transfer:

```python
sales_handoff = handoff(
    agent=sales_agent,
    on_handoff=on_sales_handoff,    # Sets new_booking=True
)
```

### 3. Dynamic Instruction Generation

Every agent's instructions are generated dynamically from the current `BotState`:

```python
def dynamic_main_instructions(ctx: RunContextWrapper[BotState], agent: Agent) -> str:
    return main_prompt(ctx.context)  # Injects persona, state, history
```

### 4. Protected Field Pattern (Negotiation)

Certain fields are system-managed and cannot be overwritten by LLM output:

```python
# NegotiationEngine enforces:
# - active_base_price: always from product catalog
# - max_discount_percent: always from config
# - current_discount_percent: never exceeds max
```

### 5. Fail-Open Guardrails

All guardrail failures default to allowing the message through:
- Input guardrail: record-only, `tripwire_triggered=False`
- Output guardrail: if the guardrail agent errors, original response passes
- System preference: availability over strictness

### 6. Session-Per-User Isolation

Each `(user_id, tenant_id)` pair maps to an isolated session with its own:
- Conversation history and summary
- Collected booking fields and contact details
- Probing state (scores, questions answered)
- Negotiation state (discounts, attempts)
- Semantic cache entries

### 7. Prompt Cache Optimization

System prompts are split into static and dynamic segments to maximize OpenAI's built-in prefix caching:

```
Message 1 (developer): [STATIC] Persona definition, rules, products  ← cached across turns
Message 2 (developer): [DYNAMIC] Current state, last agent, flags     ← changes each turn
Message 3+ (user/assistant): Conversation history
```

---

## Module Dependency Map

```
main.py
├── app_agent.py
│   ├── app/agents/factory.py
│   │   ├── app/agents/definitions.py
│   │   │   ├── app/agents/sales/
│   │   │   ├── app/agents/booking/
│   │   │   ├── app/agents/followup/
│   │   │   ├── app/agents/human_escalation/
│   │   │   ├── app/agents/negotiation/
│   │   │   ├── app/agents/objection_handle/
│   │   │   ├── app/agents/proceed_email/
│   │   │   ├── app/agents/lead_analysis/
│   │   │   ├── app/agents/brochure/
│   │   │   └── app/agents/template_generation/
│   │   └── app/agents/config.py
│   │       └── app/route/route.py (RouterModel, LiteLLM Router)
│   │
│   ├── app/core/
│   │   ├── models.py (60+ Pydantic models)
│   │   ├── guardrail.py (input/output guardrails)
│   │   ├── probing_state.py (ProbingEngineState)
│   │   ├── negotiation.py (NegotiationEngine)
│   │   └── exceptions.py
│   │
│   ├── app/database/
│   │   ├── session_manager.py (SQLite sessions)
│   │   ├── postgresql_session_manager.py (Neon PG sessions)
│   │   ├── cachememory.py (semantic cache)
│   │   ├── summarizer.py (conversation summarizer)
│   │   ├── sliding_window.py (history management)
│   │   └── executive_summary.py
│   │
│   ├── app/prompts/ (all dynamic prompt generators)
│   │
│   └── app/utils/
│       ├── prompt_cache.py (split_cached_prompt)
│       └── utils.py (convert_to_botstate, model_to_dict)
│
├── app/config/
│   ├── settings.py (Settings BaseSettings, env vars)
│   └── constants.py (AgentName enum, defaults)
│
├── rag/ (RAG pipeline — independent module)
│   ├── ETL_Pipeline/ (ingestion)
│   ├── Qdrant/ (vector DB operations)
│   └── retriever/ (search + reranking)
│
└── streamlit_ui/ (admin panel — independent module)
    ├── app.py (main Streamlit app)
    ├── chat.py (chat interface)
    ├── persona.py (persona editor)
    └── qa_panel.py (QA testing panel)
```
