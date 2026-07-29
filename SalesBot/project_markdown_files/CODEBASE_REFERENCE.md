# BotRunner Codebase Reference

> **Auto-generated comprehensive reference** for documentation purposes.  
> Covers every file path, function, class, constant, agent, handoff, tool, prompt, API endpoint, database operation, CTA trigger, scoring threshold, objection-handling rule, probing logic, negotiation flow, asset-sharing logic, and template-generation logic in the project.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Agent Definitions & Handoff Conditions](#2-agent-definitions--handoff-conditions)
3. [Agent Factory & Root Agent](#3-agent-factory--root-agent)
4. [Tools Reference](#4-tools-reference)
5. [Prompt Structures](#5-prompt-structures)
6. [Probing Logic & Scoring Thresholds](#6-probing-logic--scoring-thresholds)
7. [Objection Handling](#7-objection-handling)
8. [Negotiation Flow](#8-negotiation-flow)
9. [Demo Booking Flow](#9-demo-booking-flow)
10. [Follow-up Flow](#10-follow-up-flow)
11. [Asset Sharing Logic](#11-asset-sharing-logic)
12. [Email / Proceed-with-Email Flow](#12-email--proceed-with-email-flow)
13. [Human Escalation](#13-human-escalation)
14. [Lead Analysis](#14-lead-analysis)
15. [Template Generation](#15-template-generation)
16. [Guardrails (Input & Output)](#16-guardrails-input--output)
17. [CTA Triggers](#17-cta-triggers)
18. [Database Operations & Session Management](#18-database-operations--session-management)
19. [API Endpoints](#19-api-endpoints)
20. [Configuration & Constants](#20-configuration--constants)
21. [LLM Routing & Model Configuration](#21-llm-routing--model-configuration)
22. [Prompt Caching](#22-prompt-caching)
23. [Semantic Cache](#23-semantic-cache)
24. [RAG / Vector Search](#24-rag--vector-search)
25. [Utilities](#25-utilities)
26. [Core Models (Pydantic)](#26-core-models-pydantic)
27. [Exception Hierarchy](#27-exception-hierarchy)
28. [Callbacks](#28-callbacks)
29. [App Entry Point (app_agent.py)](#29-app-entry-point-app_agentpy)
30. [Crawl Persona Agent](#30-crawl-persona-agent)
31. [Instruction Generators](#31-instruction-generators)
32. [Dependencies & Project Metadata](#32-dependencies--project-metadata)

---

## 1. Architecture Overview

| Layer | Key Files | Purpose |
|---|---|---|
| **FastAPI server** | `main.py` | HTTP endpoints (`/chat`, `/chat_ui`, `/health`, etc.) |
| **Orchestrator** | `app_agent.py` | Session init → cache lookup → agent execution → state finalisation → persistence |
| **Agent factory** | `app/agents/factory.py` | Creates root agent with handoffs, tools, guardrails |
| **Agents** | `app/agents/*/agent.py` (13 agents) | Specialised agents for sales, booking, follow-up, probing, etc. |
| **Prompts** | `app/prompts/*.py` | Dynamic prompt generators per agent / guardrail |
| **Tools** | `app/tools/*.py` | Function tools: RAG retrieval, datetime processing, Calendly, email validation |
| **Core** | `app/core/*.py` | Pydantic models, state, guardrails, negotiation engine, probing engine |
| **Database** | `app/database/*.py` | Session persistence (SQLite / Neon PG), summarising session, semantic cache |
| **RAG** | `rag/` | Qdrant vector store, ETL pipeline, retriever with reranking |
| **Route** | `app/route/route.py` | LiteLLM Router wrapping Azure → OpenAI → Gemini fallback chain |
| **Config** | `app/config/*.py` | `Settings` (pydantic-settings), `AgentName` enum, constants |
| **Utils** | `app/utils/*.py` | Consumption tracking, prompt cache monitor, sanitisation |
| **Callbacks** | `app/callbacks/handlers.py` | Handoff callbacks that mutate `BotState` |
| **Instructions** | `app/instructions/generators.py` | `InstructionBuilder` + `PromptTemplate` for composable prompts |

### Framework Stack

- **OpenAI Agents SDK** `openai-agents[sqlalchemy]==0.10.1`
- **LiteLLM** `1.80.11` — multi-provider router
- **Opik** `1.9.69` — tracing
- **Qdrant** `1.15.1` — vector DB
- **Crawl4AI** `0.7.8` — web crawling
- **FastAPI** + **Streamlit** — API & UI
- **Pydantic** `2.12.5` — data models
- **SQLAlchemy** (async) + **psycopg2** / **asyncpg** — database

---

## 2. Agent Definitions & Handoff Conditions

### 2.1 AgentName Enum

**File:** `app/config/constants.py`

```
MAIN = "main_agent"
SALES = "sales_agent"
DEMO_BOOKING = "demo_booking_agent"
FOLLOWUP = "followup_agent"
HUMAN = "human_escalation_agent"
LEAD_ANALYSIS = "lead_analysis_agent"
OBJECTION_HANDLE = "objection_handle_agent"
PROCEED_EMAIL = "proceed_email_agent"
NEGOTIATION = "negotiation_agent"
BROCHURE = "brochure_agent"
PROBING = "probing_agent"              # standalone
PROBING_INSTRUCTION = "probing_instruction_agent"  # standalone
TEMPLATE_GENERATION = "template_generation_agent"  # standalone
```

### 2.2 Agent Handoff Descriptions

Defined in `AGENT_HANDOFF_DESCRIPTIONS` dict (`app/config/constants.py`), used as the `description_override` in every `handoff()` call:

| Target Agent | Handoff Trigger Description (summarised) |
|---|---|
| **sales_agent** | Product inquiries, feature comparisons, pricing questions, objections, generic product curiosity |
| **demo_booking_agent** | Demo/meeting booking, scheduling, CTA acceptance, rescheduling, cancellation; also when probing is complete & CTA shown |
| **followup_agent** | Follow-up scheduling, reminder requests, "call me later", re-engagement after human |
| **human_escalation_agent** | Explicit "talk to human/agent/manager", unresolvable complaints, complex issues beyond bot scope |

### 2.3 Per-Agent Details

#### sales_agent
- **File:** `app/agents/sales/agent.py`
- **Tools:** `retrieve_query`, `objection_handle_tool` (as_tool)
- **Dynamic instructions:** `sales_prompt(state)` (from `app/prompts/dynamic_sales.py`)
- **Model:** primary via `get_primary_model()`
- **Output:** `BotResponse` via `get_output_schema()`

#### demo_booking_agent
- **File:** `app/agents/booking/agent.py`
- **Tools:** `get_timezone`, `process_booking_datetime`, `lead_analysis_tool` (as_tool), `check_calendly_availability`
- **Dynamic instructions:** `booking_prompt(state)` (from `app/prompts/demo_booking.py`)
- **Model:** primary

#### followup_agent
- **File:** `app/agents/followup/agent.py`
- **Tools:** `get_timezone`, `process_followup_datetime`
- **Dynamic instructions:** `followup_prompt(state)` (from `app/prompts/followup.py`)
- **Model:** primary

#### human_escalation_agent
- **File:** `app/agents/human_escalation/agent.py`
- **Tools:** None
- **Output guardrails:** `[output_guardrail]`
- **Dynamic instructions:** `human_agent_prompt(state)` (from `app/prompts/human_agent.py`)
- **Model:** primary

#### lead_analysis_agent
- **File:** `app/agents/lead_analysis/agent.py`
- **Tools:** None (used as `.as_tool()` within demo_booking)
- **Static instructions:** `lead_analysis_prompt` (from `app/prompts/lead_analysis.py`)
- **Output:** `LeadAnalysis`

#### objection_handle_agent
- **File:** `app/agents/objection_handle/agent.py`
- **Tools:** `retrieve_query` (RAG)
- **Dynamic instructions:** `objection_handle_prompt(state)` (from `app/prompts/objection_handle.py`)
- **Output:** `BotResponse` — used as `.as_tool()` within sales_agent

#### proceed_email_agent
- **File:** `app/agents/proceed_email/agent.py`
- **Tools:** None
- **Dynamic instructions:** `proceed_with_email_prompt(state)` (from `app/prompts/proceed_with_email.py`)
- **Used as:** `.as_tool()` on root agent

#### negotiation_agent
- **File:** `app/agents/negotiation/agent.py`
- **Tools:** None
- **Output type:** `NegotiationAgentResponse`
- **Dynamic instructions:** `get_pricing_negotiation_prompt(state)` (from `app/prompts/negotiation.py`)
- **Used as:** `.as_tool()` (negotiation_engine) on root agent

#### brochure_agent (asset sharing)
- **File:** `app/agents/brochure/agent.py`
- **Tools:** None
- **Dynamic instructions:** `asset_sharing_prompt(state)` (from `app/prompts/asset_sharing.py`)
- **Output:** `BotResponse` — used as `.as_tool()` (proceed_with_asset_sharing) on root agent

#### probing_agent (standalone)
- **File:** `app/agents/probing/agent.py`
- **Entry:** `run_probing_agent(persona, total_k=5)` → `ProbingAgentResponse`
- **Model:** `LitellmModel` (gemini/gemini-3-flash-preview)
- **Not part of conversation handoff chain**

#### probing_instruction_agent (standalone)
- **File:** `app/agents/probing_instruction/agent.py`
- **Entry:** `generate_probing_question_instructions()`
- **Model:** `LitellmModel` (gemini)
- **Output:** `InstructionAgentResponse`

#### template_generation_agent (standalone)
- **File:** `app/agents/template_generation/agent.py`
- **Entry:** `run_template_generation_agent()`
- **Model:** `LitellmModel` (gemini)
- **Output:** `TemplateGenerationResponse`

#### crawl_persona_agent (standalone)
- **File:** `app/agents/crawl_persona/agent.py`
- **Entry:** `run_crawl_persona_agent()`
- **Crawls website** via Crawl4AI `BFSDeepCrawlStrategy`, cleans content, ingests into Qdrant, extracts `BotPersona`

---

## 3. Agent Factory & Root Agent

**File:** `app/agents/factory.py` (438 lines)

### AgentFactory

```python
class AgentFactory:
    _creators = {
        AgentName.SALES: create_sales_agent,
        AgentName.DEMO_BOOKING: create_demo_booking_agent,
        AgentName.FOLLOWUP: create_followup_agent,
        AgentName.HUMAN: create_human_agent,
        AgentName.LEAD_ANALYSIS: create_lead_analysis_agent,
        AgentName.OBJECTION_HANDLE: create_objection_handle_agent,
        AgentName.PROCEED_EMAIL: create_proceed_email_agent,
        AgentName.NEGOTIATION: create_negotiation_agent,
        AgentName.BROCHURE: create_asset_sharing_agent,
    }
```

### create_root_agent()

Returns `Agent[BotState]` named `"main_agent"` with:

- **Handoffs** (4): sales → demo_booking → followup → human (each with `on_handoff` callback + `HandoffArgs` input type)
- **Tools** (3 as_tool): `proceed_with_email`, `negotiation_engine`, `proceed_with_asset_sharing`
- **Input guardrails:** `[input_attack]`
- **Dynamic instructions:** `dynamic_main_instructions(context, agent)` → calls `main_prompt(state)`
- **Model:** `get_primary_model()` → `RouterModel("primary")`
- **Output schema:** `AgentOutputSchema(BotResponse, strict_json_schema=False)`

Singleton: `get_factory()` / `root_agent()`

---

## 4. Tools Reference

### 4.1 sales_tools.py

**File:** `app/tools/sales_tools.py`

| Tool | Signature | Description |
|---|---|---|
| `retrieve_query` | `(ctx, user_query: str) → str` | RAG retrieval from Qdrant. Gets `tenant_id` from `state.user_context.tenant_id`. Returns the retrieved context string. |

### 4.2 booking_tools.py

**File:** `app/tools/booking_tools.py` (1587 lines)

| Tool | Signature | Description |
|---|---|---|
| `process_booking_datetime` | `(ctx, datetime_expression: str, timezone: str) → Dict` | **Unified** datetime processing: parse → validate → convert to UTC → update state. Steps: (1) `_parse_datetime_expression()` (2) `_validate_booking_datetime()` against business rules (3) `_convert_to_utc()` (4) Updates `collected_fields.date` and `collected_fields.time`. Returns `{success, parsed, validation, utc_conversion, next_action, message}`. |
| `check_calendly_availability` | `(date_time_utc_iso: str, tenant_id: str, user_timezone: str) → Dict` | Checks Calendly for slot availability. Returns `{is_available, alternative_slots[], requested_time_local}`. Calls `calendly_available_slots_api()`. Converts slots to local timezone. |
| `validate_email` | `(email: str) → Dict` | RFC 5322 validation + domain typo detection (gmail, yahoo, outlook, hotmail variants). Returns `{is_valid, suggestion, typo_detected}`. |
| `parse_relative_datetime` | `(relative_str, timezone) → Dict` | **DEPRECATED** — wrapper for `_parse_datetime_expression()`. |
| `parse_relative_time` | `(relative_str, timezone) → Dict` | Another datetime parser (simpler variant). |
| `validate_datetime` | `(date, time_str, timezone) → Dict` | Business-rule validation only (past, weekend, working hours 10-23, >6 months). |
| `convert_time_to_utc` | `(ctx, time_str, date_str, timezone) → Dict` | Converts local → UTC, updates state. |
| `dummy_calendly_api` | `(unused) → Dict` | Testing stub. |

#### Internal helpers (not tools):

- `_parse_datetime_expression(relative_str, timezone)` — Extensive NLP datetime parser supporting: relative ("in X hours/days"), "tomorrow"/"today", weekday names, time-of-day words (morning/noon/afternoon/evening), explicit dates (multiple formats: "9th Dec", "Dec 9", "12/9/2025", "2025-12-09"), AM/PM and 24h time extraction, word-to-number (English). Defaults to 10:00 AM when time not specified (sets `time_defaulted=True`).
- `_validate_booking_datetime(date_str, time_str, timezone, working_hours)` — Validates against: past time, weekend, persona-defined working hours (or default 10:00-23:00), holidays, >6 months future.
- `_convert_to_utc(date_str, time_str, timezone)` — pytz localize → UTC.

### 4.3 followup_timezone.py

**File:** `app/tools/followup_timezone.py` (503 lines)

| Tool | Signature | Description |
|---|---|---|
| `get_timezone` | `(ctx, region_code: str) → Dict` | Looks up `pytz.country_timezones`, handles multiple timezones per country, updates `state.user_context.timezone` and `region_code`. |
| `process_followup_datetime` | `(ctx, datetime_expression: str, timezone: str) → Dict` | Extensive parser with: word-to-number conversion (English + **Hindi**), AM/PM/24h/bare hour time extraction, time-of-day references, relative patterns ("in X units", "X units later"), "half hour", "couple of hours", "quarter hour", explicit dates, weekday names. Validates: past, >90 days future. Converts to UTC. Updates `state.user_context.collected_fields["followup_time"]`. |

### 4.4 human_tools.py

**File:** `app/tools/human_tools.py`

| Tool | Signature | Description |
|---|---|---|
| `validate_email` | `(email: str) → Dict` | Regex validation, domain typo correction (gmail/yahoo/outlook/hotmail/icloud/aol/live/protonmail), suspicious pattern detection. |

---

## 5. Prompt Structures

All prompts use the `CACHE_BREAK` marker (`\n\n<!-- CACHE_BREAK -->\n\n`) to split static instructions (cached by OpenAI prefix caching) from dynamic context (per-request).

### 5.1 Main/Instruction Prompt

**File:** `app/prompts/instruction.py` → `main_prompt(state: BotState) → str`

**Structure:**
```
<identity> — Bot persona: name, company, domain, industry, goal
<personality> — From persona.personality
<rules> — From persona.rules
<products> — Product catalog with pricing, descriptions
<language_rule> — Multi-language/script matching rules
<handoff_rules> — When to hand off to each specialist agent
<critical_execution_rules> — 6 rules:
  rule_1: Handoff-first priority
  rule_2: Never interrupt specialists
  rule_3: Response never null without handoff
  rule_4: Use chat history for context
  rule_5: Generate response when uncertain
  rule_6: negotiation_engine usage rules (pricing/discount/budget)
<output_format> — JSON with response, proceed_email_details, brochure_details, user_language, user_script
<examples> — 10+ examples including greetings, Hindi, off-domain, email, asset sharing
CACHE_BREAK
<conversation_state> — user_query, flags, region, previous_agent, chat_history
```

### 5.2 Sales Prompt

**File:** `app/prompts/dynamic_sales.py` → `sales_prompt(state) → str`

**Structure:** Company identity → products → RAG-retrieved context → language rules → response format. Uses `retrieve_query` tool for knowledge base lookups.

### 5.3 Probing Prompt

**File:** `app/prompts/probing.py` → `probing_prompt(state) → str`

**Structure:**
```
<identity> — Bot persona
<probing_flow> — 8-step algorithm:
  step_1: Classify query (Category A/B/C)
  step_2: Detect language
  step_3: Product query check → use retrieve_query tool
  step_4: Check if probing already complete → show CTA
  step_5: Match answer to probing question
  step_6: Update score → check CTA threshold
  step_7: Select next question (lowest priority, mandatory first)
  step_8: Translate question to user's language/script
<critical_rules> — Stay in character, use language_rule
<output_format> — probing_details FIRST (score/CTA decision), response SECOND
<examples> — 7 examples covering threshold reached, continue, objection limit, irrelevant, vague, tool response
CACHE_BREAK
<probing_status> — Current score, threshold, objection count
<available_questions> — Unanswered questions with scores/priorities
<answered_questions> — Already answered Q/A pairs
<conversation_history>
<user_query>
<language_rule>
```

### 5.4 Demo Booking Prompt

**File:** `app/prompts/demo_booking.py` → `booking_prompt(state) → str`

**Structure:**
```
<identity>
<step_0> — Acknowledgment detection patterns
<step_1> — Intent determination (NEW/RESCHEDULE/CANCEL/CONFIRM/ACKNOWLEDGMENT/DATETIME_PROVIDED)
<step_preprocessing> — Check chat context for datetime mentions
<flow_a> — NEW booking: collect fields → process datetime → check Calendly → confirm
<flow_b> — RESCHEDULE: verify existing → process new datetime → check Calendly → update
<flow_c> — CANCEL: verify existing → confirm cancellation
<flow_d> — CONFIRMATION: already confirmed, just acknowledge
<tools> — process_booking_datetime, check_calendly_availability, lead_analysis_tool
<examples> — 12 examples covering all flows
<critical_rules> — 16 rules (Calendly determines confirmation, lead_analysis on confirm, preserve booking_type, etc.)
CACHE_BREAK
<current_state> — UTC time, timezone, products, mandatory fields
<user_query>
<existing_data> — contact, collected fields, booking status
<chat_context>
<language_rule>
```

### 5.5 Follow-up Prompt

**File:** `app/prompts/followup.py` → `followup_prompt(state) → str`

Collects follow-up scheduling with timezone detection, datetime parsing, and follow-up message generation.

### 5.6 Human Agent Prompt

**File:** `app/prompts/human_agent.py` → `human_agent_prompt(state) → str`

Escalation flow: collect summary, classify sentiment, validate email, check availability, confirm handoff.

### 5.7 Negotiation Prompt

**File:** `app/prompts/negotiation.py` → `get_pricing_negotiation_prompt(state) → str`

Pricing negotiation with discount strategies, budget-aware offers, multi-product negotiation. Uses `NegotiationConfig` (max_discount_percent, currency).

### 5.8 Objection Handle Prompt

**File:** `app/prompts/objection_handle.py` → `objection_handle_prompt(state) → str`

Classifies objections (soft/hard/hidden), generates empathetic responses, uses RAG for knowledge-backed re-engagement.

### 5.9 Proceed-with-Email Prompt

**File:** `app/prompts/proceed_with_email.py` → `proceed_with_email_prompt(state) → str`

Handles email requests: checks for available email, matches template to conversation, generates HTML reply body.

### 5.10 Asset Sharing Prompt

**File:** `app/prompts/asset_sharing.py` → `asset_sharing_prompt(state) → str`

Matches user request to available assets (from `persona.assets`). Returns asset details (id, name, path) for single match or presents options for multiple.

### 5.11 Lead Analysis Prompt

**File:** `app/prompts/lead_analysis.py` — Static prompt

Classifies leads as hot/warm/cold based on conversation context. Returns `LeadAnalysis` with classification, reasoning, key_indicators, recommended_next_action, urgency_level.

### 5.12 Input Guardrail Prompt

**File:** `app/prompts/input_guardrail.py` → `input_guardrail_prompt(state) → str`

**Classification:** `safe` vs `attack_query`

**Safe criteria:** Greetings, conversational responses (hmm, ok, sure), business inquiries about products/pricing/CTA, professional communication, contextual continuity.

**Attack criteria:** AI identity probing, prompt injection, org intelligence, competitor intelligence, hostile content, malicious intent, illegal requests, off-topic queries.

**Decision process:** 5-step: conversational check → business context → chat history → attack patterns → default. Fail-open for conversational responses.

### 5.13 Output Guardrail Prompt

**File:** `app/prompts/output_guardrail.py` → `output_guardrail_prompt(state) → str`

**12 validation rules:**
1. Domain scope — reject unauthorized products, off-domain answers
2. Information accuracy — reject fabricated features/pricing
3. Contact info — reject fabricated contacts
4. Tone & personality — match persona, ≤1 exclamation, word limits
5. Language & cultural — correct language/script
6. Bot rules compliance
7. Goal alignment
8. Booking flow — progressive collection OK, reject only if ignoring provided info
9. Data privacy — no credit cards/SSN/passwords
10. Datetime validation — require tool sequence
11. Email validation — require validate_email() call
12. Response quality — reject gibberish/hostile

**Severity logic:** CRITICAL → reject, HIGH → modify/reject, MEDIUM → modify/approve, LOW → approve. Poor but safe responses get `suggested_text` instead of rejection.

### 5.14 Other Prompts

| File | Function | Purpose |
|---|---|---|
| `app/prompts/crawl_persona.py` | `crawl_persona_prompt()` | Extract BotPersona after crawling website |
| `app/prompts/generate_probing_question.py` | `generate_probing_question_prompt()` | Generate probing questions for persona |
| `app/prompts/generate_probing_instructions.py` | `generate_probing_instructions_prompt()` | Generate probing instructions |
| `app/prompts/template_generation.py` | — | WhatsApp template generation |
| `app/prompts/executive_summary_prompt.py` | `executive_summary_prompt()` | Summarise conversation into executive summary |
| `app/prompts/summarizer_prompt.py` | — | Context window summarisation |
| `app/prompts/use_emoji.py` | `use_emoji(state)` | Emoji usage rules based on `persona.use_emoji` |
| `app/prompts/use_name.py` | `use_name(state)` | Name reference rules based on `persona.use_name_reference` |

---

## 6. Probing Logic & Scoring Thresholds

### 6.1 Probing Engine State

**File:** `app/core/probing_state.py` → `ProbingEngineState`

**Key method:** `update_probing_context(probing_details) → (ProbingContext, ObjectionState)`

**Algorithm:**

1. Track Q/A pairs in `detected_question_answer[]`
2. Accumulate `total_score` from each answered question's `score_to_add`
3. Check `total_score >= probing_threshold` → set `probing_completed=True`, `can_show_cta=True`
4. Track objections: increment `current_objection_count` when `is_objection=True`
5. Check `current_objection_count >= objection_count_limit` → set `is_objection_limit_reached=True`

**Objection reset cycle:**
- When `is_objection_limit_reached` was `True` on previous message → increment `limit_reach_count`, reset objection count to 0
- **UNLESS** `limit_reach_count >= reset_count_limit` → **FREEZE**: objection count stops incrementing, CTA disabled

### 6.2 Default Thresholds

**File:** `app/config/constants.py`

| Constant | Default | Description |
|---|---|---|
| `DEFAULT_PROBING_THRESHOLD` | 50 | Score threshold to trigger CTA |
| `DEFAULT_OBJECTION_LIMIT` | 3 | Max objections before limit reached |
| `DEFAULT_RESET_COUNT_LIMIT` | 2 | Max reset cycles before freeze |

**Per-persona overrides** in `BotPersona`:
- `probing_threshold` (default 50)
- `objection_count_limit` (default 3)
- `reset_count_limit` (default 2)

### 6.3 ProbingQuestion Model

```python
class ProbingQuestion:
    id: str
    question: str
    score: float       # Points awarded when answered
    priority: int      # Lower = asked first
    mandatory: bool    # Asked before optional questions at same priority
```

### 6.4 ProbingOutput (LLM output)

```python
class ProbingOutput:
    detected_question: str    # Exact text from available_questions
    detected_answer: str      # User's answer in their words, "" if objection
    score_to_add: float       # Score value of matched question, 0.0 if objection
    probing_completed: bool   # True if threshold met or objection limit reached
    can_show_cta: bool        # True → show CTA in response
    is_answered: bool         # True if valid answer given
    is_objection: bool        # True if user refused/objected
    reasoning: str            # Multi-step reasoning (RELEVANCE → MATCH → SCORE)
    product_id: Optional[str] # Detected product from answer
```

### 6.5 Probing Prompt Flow (8 steps)

1. **Classify query** — Category A (answer to current Q), B (objection), C (product query/off-topic)
2. **Detect language** — Track user_language and user_script
3. **Product query** → use `retrieve_query` tool, answer, then re-ask probing question
4. **Check already complete** → if `probing_completed=True`, show CTA
5. **Match answer** to probing question (semantic match to exact question text)
6. **Update score** → compute new total → check threshold → CTA rules
7. **Select next question** — lowest priority, mandatory first, exclude just-answered
8. **Translate & ask** — translate exact question to user's language/script

---

## 7. Objection Handling

### 7.1 ObjectionAnalysis Model

```python
class ObjectionAnalysis:
    type_of_objection: str  # "soft" | "hard" | "hidden"
    objection_reasoning: str
```

### 7.2 ObjectionState Model

```python
class ObjectionState:
    current_objection_count: int
    is_objection_limit_reached: bool
    limit_reach_count: int
    objection_analysis: Optional[ObjectionAnalysis]
```

### 7.3 Objection Types

| Type | Description | Example |
|---|---|---|
| **soft** | Low engagement/disinterest, recoverable | "I'm not interested" |
| **hard** | Direct refusal, strong resistance | "I don't want to answer that" |
| **hidden** | Underlying concern masked by deflection | "I'll think about it" (hiding budget concern) |

### 7.4 Objection Flow

1. Probing agent detects `is_objection=True` in user message
2. Sets `score_to_add=0.0`, `is_answered=False`
3. Calls `objection_handle_agent` tool (has RAG access)
4. Objection handler:
   - Classifies type (soft/hard/hidden)
   - Uses RAG (`retrieve_query`) for knowledge-backed response
   - Returns empathetic re-engagement response
5. Probing agent combines objection response + next probing question
6. `ProbingEngineState.update_probing_context()` increments objection count
7. If `objection_count >= objection_count_limit` → `is_objection_limit_reached=True` → show CTA
8. Reset cycle: next message after limit → `limit_reach_count++`, reset count → continue or freeze

---

## 8. Negotiation Flow

### 8.1 NegotiationEngine

**File:** `app/core/negotiation.py`

**Key methods:**

| Method | Purpose |
|---|---|
| `pre_detect_product(user_query)` | Scans query for product names/IDs. Matches via: ID → exact name → token → substring. |
| `update_negotiation_state(output_data)` | Merges LLM output into `negotiated_products[]`. **Protected fields:** `active_base_price`, `max_discount_percent` (cannot be overwritten by LLM). Monotonic `negotiation_attempts` (only increments). |
| `_find_negotiated_product()` | ID match first, name-based fallback |
| `_merge_negotiated_product()` | Protected keys preserved |
| `_add_new_negotiated_product()` | Enriches from product catalog |
| `_enforce_product_config()` | System pricing enforcement |
| `_apply_product_to_state()` | Apply detected product from probing |

### 8.2 Negotiation Models

```python
class NegotiationConfig:
    max_discount_percent: float = 5.0
    currency: str = "INR"

class NegotiatedProduct:
    product_name: str
    product_id: Optional[str]
    active_base_price: Optional[float]      # PROTECTED
    max_discount_percent: Optional[float]    # PROTECTED
    current_discount_percent: float
    final_price: Optional[float]
    negotiation_attempts: int               # MONOTONIC
    negotiation_phase: str                  # initial → active → closing
    negotiation_active: bool
    discount_locked: bool
    last_offer_response: Optional[str]
    user_budget_constraint: Optional[float]
    negotiation_discount_offered: Optional[float]
    internal_note: Optional[str]
    reasoning: str                          # REQUIRED

class NegotiationAgentResponse:
    negotiated_products: List[NegotiatedProduct]
    current_product_name: Optional[str]
    current_product_id: Optional[str]
    response: str
```

### 8.3 Main Agent negotiation_engine Rules

From the main prompt (`rule_6`):

**When to call:**
- Price mentions: "how much?", "cost?", "pricing?"
- Discount requests: "any discount?", "best price?"
- Budget objections: "too expensive", "out of budget"
- Payment terms: "installments?", "EMI?"
- Competitor comparison: "X is cheaper"
- Negotiation signals: "seems high", "can you be flexible?"
- Budget sharing: "my budget is X"

**Rules:**
- NEVER respond to pricing yourself — always call tool
- NEVER reveal discount ceiling
- NEVER make up a price
- Tool response IS the final response
- Stage-aware: first ask → pushback → deeper concession → final offer

### 8.4 Negotiation State Flow in app_agent.py

1. `NegotiationEngine.pre_detect_product()` before agent execution
2. Agent calls `negotiation_engine` tool → `NegotiationAgentResponse`
3. `finalize_bot_state()` extracts negotiation tool output from `function_call_output` items
4. `_apply_output_to_state()` → `NegotiationEngine.update_negotiation_state()`
5. `_update_negotiation_dynamic_state()` — applies product from probing context, collected fields, budget

---

## 9. Demo Booking Flow

### 9.1 Booking Fields Model

```python
class BookingFields:
    booking_type: Optional[str]      # "new" | "reschedule" | "cancel"
    booking_confirmed: bool = False   # ONLY True when Calendly confirms
    ask_new_date: bool = False
    calendly_checked: bool = False
```

### 9.2 Mandatory Fields

- `email` (from contact_details or collected)
- `products` (auto-selected from negotiated products, or asked)
- `date` (YYYY-MM-DD)
- `time` (UTC ISO 8601)

### 9.3 Flows

| Flow | Prereq | Steps |
|---|---|---|
| **Flow A — NEW** | None | Collect fields → process_booking_datetime → check_calendly → lead_analysis |
| **Flow B — RESCHEDULE** | `booking_confirmed=True` | Verify existing → process new datetime → check_calendly → update (original stays valid if new slot unavailable) |
| **Flow C — CANCEL** | `booking_confirmed=True` | Verify → confirm → set `booking_confirmed=False` |
| **Flow D — CONFIRMATION** | Already confirmed | No tools needed, just lead_analysis if not called |

### 9.4 Critical Rules

- `booking_confirmed=True` ONLY when `check_calendly_availability` returns `is_available=True`
- Always call `lead_analysis_tool` when booking confirmed (new/reschedule)
- Reschedule: keep original valid if new slot unavailable
- Extract datetime from chat context if user says "confirm" without providing it again
- Auto-select products from finalized negotiation
- Translate datetime expressions to English before tool calls

### 9.5 Working Hours

**Default persona:** Mon-Fri 10:00-19:00, Sat-Sun Holiday

**Default tool fallback:** 10:00-23:00

**Validation rejects:** Past time, weekend, outside working hours, holidays, >6 months future

---

## 10. Follow-up Flow

### 10.1 FollowupDetails Model

```python
class FollowupDetails:
    followup_flag: bool
    followup_time: Optional[str]   # UTC ISO
    followup_msg: Optional[str]
    timezone_confirmed: bool
```

### 10.2 Flow

1. Handoff from main_agent when follow-up intent detected
2. `get_timezone(region_code)` → determine timezone
3. `process_followup_datetime(datetime_expression, timezone)` → parse → validate → UTC convert
4. Store in `collected_fields["followup_time"]`
5. Generate follow-up message

### 10.3 Followup Datetime Parser Features

- Word-to-number: English + Hindi ("ek" → 1, "do" → 2, "teen" → 3, etc.)
- Time-of-day: morning (10:00), afternoon (14:00), evening (18:00), night (20:00)
- Special: "half hour", "couple of hours", "quarter hour"
- Max range: 90 days future

---

## 11. Asset Sharing Logic

### 11.1 Asset Model

```python
class Asset:
    asset_id: str
    asset_name: str
    asset_description: Optional[str]
    asset_path: str          # URL to the asset
    other_info: Optional[str]
```

### 11.2 Flow

1. User requests document/brochure/datasheet
2. Main agent calls `proceed_with_asset_sharing` tool (brochure_agent.as_tool())
3. Asset sharing prompt matches request to `persona.assets[]`:
   - **Single match** → return asset details (id, name, path) in `brochure_details`
   - **Multiple matches** → list options, ask user to choose
   - **No match** → list available assets
4. `finalize_bot_state()` extracts `brochure_details` from agent output, parses Pydantic repr strings
5. Sets `brochure_flag=True` on `BotState`

### 11.3 AssetSharedDetails Output

```python
class AssetSharedDetails:
    asset_id: Optional[str]
    asset_name: Optional[str]
    asset_path: Optional[str]
```

---

## 12. Email / Proceed-with-Email Flow

### 12.1 ProceedEmailDetails Model

```python
class ProceedEmailDetails:
    switch_to_email: bool
    email_template_id: Optional[str]
    email_template_name: Optional[str]
    get_email_flag: bool
    reply_body: Optional[str]      # HTML body
    email: Optional[str]
```

### 12.2 EmailTemplate Model

```python
class EmailTemplate:
    id: str
    name: str
    subject: str
    body: str
```

### 12.3 Flow

1. Main agent detects email request or `@` symbol in user message
2. Calls `proceed_with_email` tool (proceed_email_agent.as_tool())
3. Agent:
   - Checks if user email is available
   - If no email → asks for it (`get_email_flag=False`)
   - If email available → matches template to conversation context
   - Generates HTML `reply_body` 
   - Sets `switch_to_email=True`, `get_email_flag=True`
4. Output contains template details for backend to send actual email

---

## 13. Human Escalation

### 13.1 HumanDetails Model

```python
class HumanDetails:
    summary: Optional[str]
    key_topics: Optional[List[str]]
    user_sentiment: Optional[str]
    unresolved_issues: Optional[List[str]]
    user_intent: Optional[str]
    email_validated: Optional[bool]
    email_suggestion: Optional[str]
    priority: Optional[str]
    ready_for_handoff: Optional[bool]
    human_availability_checked: Optional[bool]
    human_preferred_time: Optional[str]
    human_slot_confirmed: Optional[bool]
    human_slot_details: Optional[str]
    human_availability_window: Optional[str]
```

### 13.2 Flow

1. User says "talk to human/agent/manager" or unresolvable issue detected
2. Main agent hands off to `human_escalation_agent` via `on_human_handoff` callback
3. Callback sets: `human_requested=True`, `escalation_timestamp=utc_now`, `last_agent=HUMAN`
4. Human agent: collects summary, classifies sentiment, validates email
5. Has `output_guardrails=[output_guardrail]` — responses are validated

---

## 14. Lead Analysis

### 14.1 LeadAnalysis Model

```python
class LeadAnalysis:
    lead_classification: str    # "hot" | "warm" | "cold"
    reasoning: str
    key_indicators: List[str]
    recommended_next_action: str
    urgency_level: str
```

### 14.2 Usage

- Called as `.as_tool()` within `demo_booking_agent` after successful booking confirmation
- Uses static prompt with conversation context
- Not called for cancellations
- Not called when `booking_confirmed=False`

---

## 15. Template Generation

### 15.1 Models

```python
class WhatsAppTemplate:
    template_name: str
    category: str
    language: str
    header: Optional[str]
    body: str
    footer: Optional[str]
    buttons: Optional[List[TemplateButton]]

class TemplateButton:
    type: str
    text: str
    url: Optional[str]
    phone_number: Optional[str]

class TemplateGenerationResponse:
    templates: List[WhatsAppTemplate]
    reasoning: str
```

### 15.2 Flow

- Standalone agent (not in conversation handoff chain)
- Called via `/generate_templates` API endpoint
- Uses `LitellmModel` (Gemini)
- Generates WhatsApp message templates based on persona/product context

---

## 16. Guardrails (Input & Output)

### 16.1 Input Guardrail

**File:** `app/core/guardrail.py`

**Fast path:** `SAFE_CONVERSATIONAL_PATTERNS` set (greetings, acknowledgments, fillers like "ok", "hmm", "yes", "hi", "thanks") — bypasses LLM entirely.

`_is_safe_conversational_pattern(query)` — normalises text, collapses repeated chars, checks against set.

**Slow path:** Runs `Runner.run(input_guardrail_agent)` with `InputGuardrail` output type.

**Key:** `tripwire_triggered` is always `False` — record-only mode (doesn't block, just records the classification in state as `input_guardrail_decision`).

### 16.2 Output Guardrail

**Decorator:** `@output_guardrail_decorator`

Runs `Runner.run(output_guardrail_agent)` on `BotResponse.response`.

**Trip logic:** If `validation_status_approved == "no"` → `tripwire_triggered=True` → triggers `OutputGuardrailTripwireTriggered` exception.

**Handling in app_agent.py:** Catches `OutputGuardrailTripwireTriggered`, extracts `suggested_text` from guardrail output, uses it as the response.

**Fail-open:** Guardrail errors return `tripwire_triggered=False`.

### 16.3 Guardrail Models

```python
class InputGuardrail:
    is_attack_query: bool
    reason: str
    classification: Optional[str]

class OutputGuardrail:
    validation_status_approved: str  # "yes" | "no"
    issue: Optional[str]
    original_text: Optional[str]
    suggested_text: Optional[str]
    reasoning: Optional[str]
```

---

## 17. CTA Triggers

CTA (Call-to-Action) is defined per persona as `current_cta` (e.g., "Book a Demo").

### 17.1 When CTA is Shown

| Condition | Result |
|---|---|
| `total_score >= probing_threshold` | ✅ Show CTA |
| `objection_count >= objection_count_limit` | ✅ Show CTA (limit reached) |
| `probing_completed=True` (from previous turn) | ✅ Show CTA |
| Score below threshold AND no objection limit | ❌ Continue probing |
| FROZEN state (`limit_reach_count >= reset_count_limit`) | ❌ CTA disabled |

### 17.2 CTA in Output

`ProbingOutput.can_show_cta` = `True` → response includes CTA text.

When CTA shown and user accepts → handoff to `demo_booking_agent` (or appropriate agent based on CTA type).

---

## 18. Database Operations & Session Management

### 18.1 Session Managers

**File:** `app/database/session_manager.py`

| Manager | Backend | Usage |
|---|---|---|
| `SQLiteSessionManager` | SQLite file (`data/chat_history.db`) | Local/dev |
| `NeonSessionManager` | PostgreSQL via `psycopg2.pool.SimpleConnectionPool` | Production (Neon) |

Selected by `Settings().database_type` via `get_session_manager()`.

**Operations:**
- `init_memory_db()` — create tables
- `save_state(user_id, state)` — serialise `BotState` to JSON, upsert
- `load_state(user_id)` — deserialise JSON back to `BotState`
- `get_or_create_session(user_id)` — load or create new with default `NegotiationState`

**Serialisation:** `PydanticEncoder` for JSON, `deserialize_to_botstate()` reconstructs nested Pydantic models from JSON.

### 18.2 SQLAlchemy Async Session

**File:** `app/database/agent_session.py`

- Shared async engine via `create_async_engine()`
- `get_agent_session(user_id)` → `SQLAlchemySession`
- `dispose_engine()` for shutdown

### 18.3 Context-Limited Session

**File:** `app/database/postgresql_session_manager.py`

`ContextLimitedSession` wraps `SQLAlchemySession`:
- Context window limit (`session_context_window_size=10`)
- `_validate_tool_chains()` — removes orphaned tool messages (tool_call without matching tool response)

### 18.4 Summarising Session

**File:** `app/database/summarizer.py`

`SummarizingSession` — keeps last N user turns verbatim, summarises older turns:
- `_summarize_decision_locked()` — computes boundary
- Triggers async `LLMSummarizer.summarize(messages)`
- Produces synthetic user→assistant summary pair
- Settings: `summarize_keep_last_n_turns`, `summarize_context_length`

`LLMSummarizer` — uses `router.acompletion()` with summarizer model.

### 18.5 Sliding Window Session

**File:** `app/database/sliding_window.py`

`SlidingWindowSession(SessionABC)` — wraps `SQLiteSession`, enforces window by trimming after every `add_items()`.

### 18.6 Executive Summary

**File:** `app/database/executive_summary.py`

`generate_executive_summary(agent_result, chat_history, model="summarizer")` — uses `router.acompletion()` with prompt cache splitting.

### 18.7 SQLAlchemy Model

**File:** `app/database/models.py`

```python
class SessionState(Base):
    __tablename__ = "session_states"
    user_id: str       # PK
    state_json: Text
    created_at: DateTime
    updated_at: DateTime
```

---

## 19. API Endpoints

**File:** `main.py` (FastAPI)

| Endpoint | Method | Input | Output | Description |
|---|---|---|---|---|
| `/chat` | POST | `BotRequest` | `APIResponse` | Main chat endpoint. `convert_to_botstate()` → `run_chatbot_api()` → response |
| `/chat_ui` | POST | `BotRequest` | Full `BotState` dict | For Streamlit UI — returns complete state |
| `/generate_executive_summary` | POST | `ExecutiveSummaryRequest` | Summary | Calls `generate_executive_summary()` |
| `/generate_probing_questions` | POST | `ProbingRequest` | `ProbingAgentResponse` | Calls `run_probing_agent()` |
| `/autofill_persona` | POST | `AutofillPersonaRequest` | `BotPersona` | Calls `run_crawl_persona_agent()` |
| `/generate_instructions` | POST | `InstructionAgentRequest` | `InstructionAgentResponse` | Calls `generate_probing_question_instructions()` |
| `/generate_templates` | POST | `TemplateGenerationRequest` | `TemplateGenerationResponse` | Calls `run_template_generation_agent()` |
| `/health` | GET | — | Status | Health check |
| `/cache_stats` | GET/POST | — | Stats | Prompt cache statistics |

### 19.1 BotRequest Schema

```python
class BotRequest:
    user_id: str
    tenant_id: str
    user_query: str
    bot_persona: Optional[BotPersona]
    user_context: Optional[UserContextRequest]
```

### 19.2 APIResponse Schema

```python
class APIResponse:
    response: str
    user_language: Optional[str]
    user_script: Optional[str]
    lead_details: Optional[Leads]
    contact_details: Optional[ContactDetails]
    collected_fields: Optional[CollectedFields]
    followup_details: Optional[FollowupDetails]
    proceed_email_details: Optional[ProceedEmailDetails]
    booking_fields: Optional[BookingFields]
    probing_details: Optional[ProbingContext]
    negotiation_details: Optional[NegotiationState]
    human_details: Optional[HumanDetails]
    brochure_details: Optional[AssetSharedDetails]
    consumption_info: Optional[ConsumptionInfo]
    input_guardrail_decision: Optional[InputGuardrail]
```

---

## 20. Configuration & Constants

### 20.1 Settings

**File:** `app/config/settings.py` — `Settings(BaseSettings)` loaded from `.env`

| Setting | Default | Description |
|---|---|---|
| `primary_model` | `"azure/gpt-5.1-chat"` | Main LLM |
| `guardrail_model` | `"azure/gpt-4.1-nano"` | Guardrail LLM |
| `summarizer_model` | `"azure/gpt-4.1-nano"` | Summariser LLM |
| `session_context_window_size` | `10` | Context window for session |
| `enable_prompt_caching` | `True` | OpenAI prefix caching |
| `max_history` | `15` | Max chat history messages |
| `sqlalchemy_database_url` | `":memory:"` | Database URL |
| `database_type` | — | `"sqlite"` or `"neon"` |
| `summarize_keep_last_n_turns` | — | Turns to keep verbatim |
| `summarize_context_length` | — | Context limit for summariser |

### 20.2 Constants

**File:** `app/config/constants.py`

| Constant | Value | Description |
|---|---|---|
| `MAX_HISTORY` | 15 | Max chat history entries |
| `DEFAULT_PROBING_THRESHOLD` | 50 | Score to trigger CTA |
| `DEFAULT_OBJECTION_LIMIT` | 3 | Objections before limit |
| `DEFAULT_RESET_COUNT_LIMIT` | 2 | Reset cycles before freeze |
| `EMOJI` | dict | Emoji mapping |

**Enums:**
- `AgentName` (13 values)
- `BookingType`: `NEW`, `RESCHEDULE`, `CANCEL`
- `LeadClassification`: `HOT`, `WARM`, `COLD`
- `UrgencyLevel`: levels of urgency
- `AttackClassification`: input guardrail classifications

---

## 21. LLM Routing & Model Configuration

### 21.1 RouterModel

**File:** `app/route/route.py`

`RouterModel(LitellmModel)` — overrides `_fetch_response()`:

1. Converts agent messages via `Converter.items_to_messages()`
2. Splits system instructions for prompt caching (static + dynamic parts)
3. Converts tools and handoffs
4. Handles structured output schema (JSON schema response format)
5. Calls `router.acompletion()` instead of `litellm.acompletion`
6. Records prompt cache stats via `cache_monitor.record()`

**Model settings:** `_is_gpt5_model()` → `reasoning_effort="medium"` for GPT-5, else `temperature=0.7`.

### 21.2 MODEL_LIST (7 deployments)

| Role | Model | Provider |
|---|---|---|
| Primary | `azure/gpt-5.1-chat` | Azure OpenAI |
| Primary fallback | `gpt-5.1-chat-latest` | OpenAI |
| Primary fallback 2 | `gemini/gemini-3-flash-preview` | Google |
| Guardrail | `azure/gpt-4.1-nano` | Azure OpenAI |
| Guardrail fallback | `gpt-4.1-nano` | OpenAI |
| Summarizer | `azure/gpt-4.1-nano` | Azure OpenAI |
| Summarizer fallback | `gpt-4.1-nano` | OpenAI |

**Fallback chain:** Primary → OpenAI → Gemini (per role).

### 21.3 Agent Model Configuration

**File:** `app/agents/config.py`

- `get_primary_model()` → `RouterModel("primary")`
- `get_model_settings()` → `ModelSettings()`
- `get_output_guardrails()` → `[output_guardrail]`
- `get_output_schema()` → `AgentOutputSchema(BotResponse, strict_json_schema=False)`

---

## 22. Prompt Caching

**File:** `app/utils/prompt_cache.py`

### Marker

```python
CACHE_BREAK = "\n\n<!-- CACHE_BREAK -->\n\n"
```

### Functions

| Function | Purpose |
|---|---|
| `split_cached_prompt(instructions)` | Splits on `CACHE_BREAK` → `(static_part, dynamic_part)` |
| `build_cached_messages(instructions, user_msg)` | Creates two system messages for OpenAI prefix caching |
| `split_direct_call_messages(system_prompt)` | For direct `router.acompletion()` calls (executive summary, etc.) |

### PromptCacheMonitor

`CacheStats` dataclass tracks per-request: model, cached_tokens, total_prompt_tokens, completion_tokens, cache_hit_rate, estimated_savings_pct.

`PromptCacheMonitor`:
- `record(response, model)` — extracts `cached_tokens` from response usage
- `get_stats()` → overall hit rate, request hit rate, estimated cost savings
- `get_summary()` → human-readable string

Global instance: `cache_monitor`

---

## 23. Semantic Cache

**File:** `app/database/cachememory.py`

- **Azure OpenAI embeddings** via `AzureOpenAI` client
- `SESSION_CACHE` global dict — per-session `deque` of Q/A pairs (max 15)
- `init_session(session_id)` — create empty deque
- `update_session(session_id, user_msg, assistant_msg, full_result, state)` — store pair with embedding
- `retrieve_from_cache(session_id, user_query)` — cosine similarity lookup
  - **Threshold:** 0.5
  - **Top-K:** 3
  - Returns best match if above threshold

Used in `run_chatbot_api()`: check cache before agent execution, update cache after.

---

## 24. RAG / Vector Search

### 24.1 Retriever

**File:** `rag/retriever/retriever.py`

`Retriever` class:
- `AdvanceEmbeddings` for dense vectors + reranking
- `retrieve(query, tenant_id)` → search Qdrant collection by `tenant_id` → rerank → return
- `retrieve_General_QA()` for QA-specific collections

### 24.2 ETL Pipeline

**File:** `rag/ETL_Pipeline/process_json.py` — `ETLPipeLine` for ingesting data into Qdrant.

### 24.3 Qdrant Initializer

**File:** `rag/Qdrant_initializer.py` — Setup scripts for Qdrant collections.

### 24.4 Usage in Tools

- `retrieve_query` tool (sales_tools.py) calls `Retriever().retrieve(query, tenant_id)`
- Used in `sales_agent` and `objection_handle_agent`

---

## 25. Utilities

### 25.1 utils.py

**File:** `app/utils/utils.py` (418 lines)

| Function | Purpose |
|---|---|
| `convert_to_toon(data)` | Uses `toon.encode()` for encoding |
| `format_chat_history()` | Pairs messages for display |
| `model_to_dict()` | Recursive Pydantic/dataclass → dict |
| `is_meaningful(val)` | Checks for non-default values |
| `convert_to_botstate(fastapi_request)` | Loads/creates session, merges meaningful request fields into existing state |
| `get_consumption_info(raw_responses, agent_name, primary_model, tags)` | Extracts token usage per response. Maps `_stage_name` to label. Detects tool calls. Aggregates individual + total consumption. |
| `get_individual_token_usage(state, result, latest_agent)` | Backward-compatible wrapper. Merges main + additional raw responses (input guardrails → main → output guardrails). Tags stage names. |
| `sanitize_response(text)` | Removes `**` (bold markdown) and `—`/`–` (em/en dashes) |

### 25.2 prompt_cache.py

See [Section 22](#22-prompt-caching).

---

## 26. Core Models (Pydantic)

**File:** `app/core/models.py` (1611 lines)

### Key Models

| Model | Fields | Purpose |
|---|---|---|
| `Products` | id, name, description, base_pricing, currency, max_discount_percent | Product catalog |
| `Asset` | asset_id, asset_name, asset_description, asset_path, other_info | Downloadable assets |
| `InputGuardrail` | is_attack_query, reason, classification | Input security check |
| `OutputGuardrail` | validation_status_approved, issue, original_text, suggested_text, reasoning | Output quality check |
| `CollectedFields` | name, email, phone, date, time, products | Booking collected data |
| `ContactDetails` | name, email, phone (+ `.get()` method) | User contact info |
| `Leads` | name, email, phone, products, date, time | Lead data |
| `LeadAnalysis` | lead_classification, reasoning, key_indicators, recommended_next_action, urgency_level | Lead scoring |
| `ProbingQuestion` | id, question, score, priority, mandatory | Single probing question |
| `ProbingContext` | detected_question_answer[], total_score, probing_completed, can_show_cta, is_objection, detected_product_id | Probing state |
| `ProbingOutput` | detected_question, detected_answer, score_to_add, probing_completed, can_show_cta, is_answered, is_objection, reasoning, product_id | LLM output |
| `ObjectionAnalysis` | type_of_objection, objection_reasoning | Objection classification |
| `ObjectionState` | current_objection_count, is_objection_limit_reached, limit_reach_count, objection_analysis | Objection tracking |
| `FollowupDetails` | followup_flag, followup_time, followup_msg, timezone_confirmed | Follow-up scheduling |
| `EmailTemplate` | id, name, subject, body | Email templates |
| `ProceedEmailDetails` | switch_to_email, email_template_id/name, get_email_flag, reply_body, email | Email flow state |
| `AssetSharedDetails` | asset_id, asset_name, asset_path | Shared asset details |
| `NegotiationConfig` | max_discount_percent (5.0), currency ("INR") | Negotiation limits |
| `NegotiatedProduct` | product_name/id, active_base_price, max_discount_percent, current_discount_percent, final_price, negotiation_attempts, negotiation_phase, negotiation_active, discount_locked, last_offer_response, user_budget_constraint, negotiation_discount_offered, internal_note, reasoning | Per-product negotiation state |
| `NegotiationAgentResponse` | negotiated_products[], current_product_name/id, response | Negotiation agent output |
| `NegotiationState` | negotiation_config, internal_note, negotiation_session | Full negotiation state |
| `BookingFields` | booking_type, booking_confirmed, ask_new_date, calendly_checked | Booking state |
| `HumanDetails` | summary, key_topics, user_sentiment, unresolved_issues, user_intent, email_validated, email_suggestion, priority, ready_for_handoff, human_availability_checked, human_preferred_time, human_slot_confirmed, human_slot_details, human_availability_window | Human escalation state |
| `WorkingHours` | day, type ("Working"/"Holiday"), start_time, end_time | Business hours |
| `Management` | name, designation, email, phone_number | Company management |
| `BotPersona` | Full persona config (see below) | Persona configuration |
| `UserContext` | Full user context (see below) | Per-request context |
| `BotState` | user_context, bot_persona, session_id, conversation_id, input_guardrail_decision, response, probing_context, objection_state, negotiation_state, additional_raw_responses, brochure_flag, brochure_details, consumption_info | Main state object |
| `BotResponse` | probing_details (FIRST), objection_analysis, user_language, user_script, reasoning, response (sanitized), booking_confirmed, lead_details, contact_details, timezone, region_code, collected_fields, all_info_collected, new_booking, followup_details, proceed_email_details, output_guardrail, booking_fields, negotiation_details, human_details, brochure_details | Agent output schema |
| `ConsumptionInfo` | request_timestamp, agent_name, primary_model, tags, responses[], individual_consumption{}, totals{} | Token usage tracking |
| `LLMResponseDetail` | response_index, model_name, stage_name, input/output/cached/total_tokens | Per-response usage |

### BotPersona Key Fields

```python
class BotPersona:
    name: str
    industry: Optional[str]
    category: Optional[str]
    company_name: str
    company_domain: str
    company_description: Optional[str]
    company_products: List[Products]
    core_usps: Optional[List[str]]
    core_features: Optional[List[str]]
    contact_info: Optional[Dict]
    language: Optional[str]
    rules: Optional[List[str]]
    personality: Optional[str]
    business_focus: Optional[str]
    goal_type: Optional[str]
    use_emoji: Optional[bool]
    use_name_reference: Optional[bool]
    probing_questions: Optional[List[ProbingQuestion]]
    probing_threshold: int = 50
    enable_probing: Optional[bool]
    current_cta: Optional[str]
    objection_count_limit: int = 3
    reset_count_limit: int = 2
    working_hours: Optional[List[WorkingHours]]  # Default: Mon-Fri 10:00-19:00
    company_management: Optional[List[Management]]
    negotiation_config: Optional[NegotiationConfig]
    assets: Optional[List[Asset]]
    email_template: Optional[List[EmailTemplate]]
```

### UserContext Key Fields

```python
class UserContext:
    user_id: str
    message_id: str  # auto UUID
    user_query: str
    tenant_id: Optional[str]
    chat_summary: Optional[str]
    executive_summary: Optional[str]
    chat_history: Optional[str]
    contact_details: Optional[ContactDetails]
    lead_details: Optional[Leads]
    follow_trigger: Optional[bool]
    timezone: Optional[str]
    region_code: Optional[str]
    collected_fields: Optional[Dict]
    booking_confirmed: Optional[bool]
    new_booking: Optional[bool]
    last_agent: Optional[str]
    agent_result: Optional[str]
    human_requested: Optional[bool]
    escalation_timestamp: Optional[str]
    followup_details: Optional[FollowupDetails]
    proceed_email_details: Optional[ProceedEmailDetails]
    probing_details: Optional[ProbingOutput]
    objection_analysis: Optional[ObjectionAnalysis]
    human_details: Optional[HumanDetails]
    user_language: Optional[str]
    user_script: Optional[str]
```

---

## 27. Exception Hierarchy

**File:** `app/core/exceptions.py` (593 lines)

```
BotRunnerException (base)
├── ConfigurationError
│   ├── MissingEnvironmentVariableError
│   └── InvalidConfigurationError
├── StateError
│   ├── StateValidationError
│   ├── StateSerializationError
│   └── SessionNotFoundError
├── AgentError
│   ├── AgentCreationError
│   ├── AgentExecutionError
│   ├── AgentHandoffError
│   └── AgentTimeoutError
├── GuardrailError
│   ├── InputGuardrailError
│   └── OutputGuardrailError
├── ToolError
│   ├── ToolExecutionError
│   └── ToolValidationError
├── DatabaseError
│   ├── DatabaseConnectionError
│   └── DatabaseOperationError
├── ExternalServiceError
│   ├── LLMProviderError
│   ├── VectorDBError
│   └── CalendlyError
├── ProbingError
│   └── ProbingQuestionGenerationError
└── BookingError
    ├── BookingValidationError
    └── SlotUnavailableError
```

**Utility:** `handle_exception(exception, context)` — wraps any exception into `BotRunnerException`.

---

## 28. Callbacks

**File:** `app/callbacks/handlers.py`

All callbacks accept `(ctx: RunContextWrapper[BotState], Args: HandoffArgs)`:

| Callback | Triggers | State Mutations |
|---|---|---|
| `on_sales_handoff` | Handoff to sales_agent | `new_booking=True`, updates `user_language`/`user_script` |
| `on_demo_handoff` | Handoff to demo_booking_agent | `new_booking=True`, updates `user_language`/`user_script` |
| `on_followup_handoff` | Handoff to followup_agent | `follow_trigger=True`, updates `user_language`/`user_script` |
| `on_human_handoff` | Handoff to human_escalation_agent | `human_requested=True`, `escalation_timestamp=utc_now`, `last_agent=AgentName.HUMAN.value` |

`HandoffArgs` model:
```python
class HandoffArgs:
    user_language: Optional[str]
    user_script: Optional[str]
```

`CallbackRegistry` class for centralized handler management.

---

## 29. App Entry Point (app_agent.py)

**File:** `app_agent.py` (1131 lines)

### Key Functions

| Function | Purpose |
|---|---|
| `create_default_context(user_id)` | Creates `UserContext` with defaults |
| `create_bot_state(user_id, persona)` | Creates `BotState` with `NegotiationState` |
| `run_chatbot_api(state)` | **Main entry:** init session/cache → semantic cache check → pre-detect product → build input → `Runner.run()` → finalize → save → update cache → log stats |
| `_execute_agent()` | Runs `Runner.run(root_agent(), input, context)`. Handles `OutputGuardrailTripwireTriggered` (extracts suggested_text). Creates `FallbackResult` for null response. |
| `finalize_bot_state(state, result, user_query)` | Resets brochure flags → extract output data → update metadata/last_agent → apply output → extract negotiation tool output → extract asset sharing tool output → update negotiation state → generate contextual fallback → update chat history → update probing context → build ConsumptionInfo |
| `_extract_output_data(result)` | `result.final_output.model_dump()` |
| `_apply_output_to_state(state, data)` | Recursively applies output fields. Special: `negotiation_details` → `NegotiationEngine`, `brochure_details` → brochure_flag |
| `_update_chat_history()` | Appends user/assistant/last_agent, trims to `MAX_HISTORY` |
| `_update_probing_context()` | Calls `ProbingEngineState.update_probing_context()` |
| `_update_negotiation_dynamic_state()` | `NegotiationEngine` → apply product from probing, collected fields, budget |

### Execution Flow

```
1. Init session (get_or_create_session, get_agent_session)
2. Init semantic cache
3. Check semantic cache → if hit, return cached
4. Pre-detect product via NegotiationEngine
5. Build agent input (user_query + chat_summary)
6. Execute: Runner.run(root_agent, input, context, run_config)
7. Finalize state (extract output, apply state changes, update history)
8. Save to DB
9. Update semantic cache
10. Log prompt cache stats
```

---

## 30. Crawl Persona Agent

**File:** `app/agents/crawl_persona/agent.py` (405 lines)

### Flow

1. `run_crawl_persona_agent(request: AutofillPersonaRequest)`
2. Crawls website URL via Crawl4AI with `BFSDeepCrawlStrategy`
3. Cleans/deduplicates crawled content
4. Ingests into Qdrant via `ETLPipeLine`
5. Extracts `BotPersona` from crawled content using LLM

### Key Features

- `BFSDeepCrawlStrategy` with configurable depth
- Content cleaning and deduplication
- Automatic Qdrant collection creation per tenant
- Returns fully populated `BotPersona` with company products, USPs, features

---

## 31. Instruction Generators

**File:** `app/instructions/generators.py`

### InstructionBuilder

`InstructionBuilder(state: BotState)` with methods:
- `build_main_instructions()` — for main_agent
- `build_sales_instructions()` — for sales_agent
- `build_demo_instructions()` — for demo_booking_agent
- `build_followup_instructions()` — for followup_agent
- `build_human_instructions()` — for human_escalation_agent
- `build_proceed_email_instructions()` — for proceed_email_agent

### PromptTemplate

Variable substitution engine: `{variable}` replacement from context dict.

### CompositePromptBuilder

Builds multi-section prompts from ordered sections.

### Helper Formatters

- `format_chat_history(history)` — pairs into user/assistant turns
- `format_collected_fields(fields)` — key: value pairs
- `format_products(products)` — product catalog formatting

---

## 32. Dependencies & Project Metadata

**File:** `pyproject.toml`

```toml
[project]
name = "OpenAI-SDK-Salesbot"
version = "0.1.0"
requires-python = ">=3.10"
```

### Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| `openai-agents[sqlalchemy]` | 0.10.1 | Agent framework |
| `litellm` | 1.80.11 | Multi-provider router |
| `opik` | 1.9.69 | Tracing & observability |
| `qdrant-client` | 1.15.1 | Vector database |
| `crawl4ai` | 0.7.8 | Web crawling |
| `fastapi` | latest | HTTP API |
| `streamlit` | latest | UI |
| `pydantic` | 2.12.5 | Data models |
| `asyncpg` | latest | Async PostgreSQL |
| `psycopg2-binary` | latest | Sync PostgreSQL |
| `docling` | latest | Document processing |
| `pytz` | latest | Timezone handling |

---

## File Index

| File Path | Line Count | Primary Contents |
|---|---|---|
| `main.py` | ~500 | FastAPI app, 8 endpoints |
| `app_agent.py` | 1131 | Main orchestrator, run_chatbot_api |
| `app/agents/config.py` | ~50 | Model/settings getters |
| `app/agents/definitions.py` | ~30 | Re-exports, dynamic_main_instructions |
| `app/agents/factory.py` | 438 | AgentFactory, create_root_agent |
| `app/agents/sales/agent.py` | ~40 | Sales agent creator |
| `app/agents/booking/agent.py` | ~50 | Demo booking agent creator |
| `app/agents/followup/agent.py` | ~40 | Followup agent creator |
| `app/agents/human_escalation/agent.py` | ~40 | Human agent creator |
| `app/agents/lead_analysis/agent.py` | ~30 | Lead analysis agent |
| `app/agents/objection_handle/agent.py` | ~40 | Objection handler |
| `app/agents/proceed_email/agent.py` | ~35 | Proceed email agent |
| `app/agents/negotiation/agent.py` | ~40 | Negotiation agent |
| `app/agents/brochure/agent.py` | ~40 | Asset sharing agent |
| `app/agents/probing/agent.py` | ~80 | Standalone probing agent |
| `app/agents/probing_instruction/agent.py` | ~60 | Standalone instruction generator |
| `app/agents/template_generation/agent.py` | ~60 | Standalone template generator |
| `app/agents/crawl_persona/agent.py` | 405 | Web crawler + persona extraction |
| `app/tools/sales_tools.py` | ~30 | retrieve_query tool |
| `app/tools/booking_tools.py` | 1587 | Datetime processing, Calendly, email validation |
| `app/tools/followup_timezone.py` | 503 | Timezone + followup datetime tools |
| `app/tools/human_tools.py` | ~60 | Email validation |
| `app/callbacks/handlers.py` | ~100 | 4 handoff callbacks + CallbackRegistry |
| `app/core/models.py` | 1611 | All Pydantic models |
| `app/core/state.py` | ~40 | Re-exports from models |
| `app/core/probing_state.py` | ~150 | ProbingEngineState |
| `app/core/negotiation.py` | ~300 | NegotiationEngine |
| `app/core/guardrail.py` | 547 | Input/output guardrails |
| `app/core/exceptions.py` | 593 | Exception hierarchy |
| `app/core/request_context.py` | ~20 | ContextVar for user_id |
| `app/config/settings.py` | ~80 | Settings(BaseSettings) |
| `app/config/constants.py` | ~100 | AgentName, defaults, enums |
| `app/config/__init__.py` | ~30 | Global settings instance |
| `app/route/route.py` | 304 | RouterModel, MODEL_LIST, fallbacks |
| `app/database/session_manager.py` | ~300 | SQLite + Neon session managers |
| `app/database/cachememory.py` | ~200 | Semantic cache |
| `app/database/executive_summary.py` | ~50 | Executive summary generation |
| `app/database/summarizer.py` | 357 | LLMSummarizer + SummarizingSession |
| `app/database/sliding_window.py` | ~50 | Sliding window session |
| `app/database/models.py` | ~30 | SQLAlchemy SessionState model |
| `app/database/agent_session.py` | ~50 | Async engine + session factory |
| `app/database/postgresql_session_manager.py` | ~100 | ContextLimitedSession |
| `app/instructions/generators.py` | ~200 | InstructionBuilder + templates |
| `app/utils/utils.py` | 418 | Consumption tracking, state conversion |
| `app/utils/prompt_cache.py` | 372 | CACHE_BREAK, PromptCacheMonitor |
| `app/prompts/instruction.py` | 870 | Main agent prompt |
| `app/prompts/dynamic_sales.py` | ~200 | Sales agent prompt |
| `app/prompts/probing.py` | 575 | Probing agent prompt |
| `app/prompts/demo_booking.py` | 1162 | Demo booking prompt |
| `app/prompts/followup.py` | ~200 | Followup prompt |
| `app/prompts/human_agent.py` | ~200 | Human escalation prompt |
| `app/prompts/negotiation.py` | ~300 | Negotiation prompt |
| `app/prompts/objection_handle.py` | ~200 | Objection handle prompt |
| `app/prompts/proceed_with_email.py` | ~200 | Email prompt |
| `app/prompts/asset_sharing.py` | ~150 | Asset sharing prompt |
| `app/prompts/lead_analysis.py` | ~50 | Lead analysis prompt |
| `app/prompts/input_guardrail.py` | 386 | Input guardrail prompt |
| `app/prompts/output_guardrail.py` | 213 | Output guardrail prompt |
| `app/prompts/use_emoji.py` | ~20 | Emoji usage rules |
| `app/prompts/use_name.py` | ~20 | Name reference rules |
| `app/apis/calendly_api.py` | 211 | Calendly API (currently mocked) |
| `rag/retriever/retriever.py` | ~100 | Qdrant retriever + reranking |
| `rag/main_runner.py` | ~258 | ETL pipeline runner |
| `pyproject.toml` | ~50 | Project metadata + deps |
