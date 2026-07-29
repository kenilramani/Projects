# BotRunner API Reference

> **Last Updated:** March 6, 2026 &nbsp;|&nbsp; **Version:** 2.1.0  
> **Base URL:** `http://localhost:8000` (development) / `https://<your-domain>` (production)  
> **Framework:** FastAPI &nbsp;|&nbsp; **Authentication:** None by default (add via middleware)

---

## Table of Contents

- [Overview](#overview)
- [Endpoints Summary](#endpoints-summary)
- [1. Health Check](#1-health-check)
- [2. Chat (Production)](#2-chat-production)
- [3. Chat UI (Streamlit)](#3-chat-ui-streamlit)
- [4. Generate Executive Summary](#4-generate-executive-summary)
- [5. Generate Probing Questions](#5-generate-probing-questions)
- [6. Autofill Persona](#6-autofill-persona)
- [7. Generate Instructions](#7-generate-instructions)
- [8. Generate Templates](#8-generate-templates)
- [9. Cache Stats](#9-cache-stats)
- [10. Reset Cache Stats](#10-reset-cache-stats)
- [Data Models Reference](#data-models-reference)
- [Error Handling](#error-handling)
- [Rate Limits & Performance](#rate-limits--performance)

---

## Overview

BotRunner exposes a RESTful API via FastAPI. All POST endpoints accept and return JSON. The API is stateful — each `(user_id, tenant_id)` pair maps to a persistent session that tracks conversation history, collected fields, and agent state.

**Server startup:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Interactive docs (auto-generated):**
- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`
- OpenAPI JSON: `GET /openapi.json`

---

## Endpoints Summary

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| `GET` | [`/health`](#1-health-check) | Health check | None |
| `POST` | [`/chat`](#2-chat-production) | Main chat endpoint (returns `APIResponse`) | None |
| `POST` | [`/chat_ui`](#3-chat-ui-streamlit) | Streamlit UI endpoint (returns full `BotState` dict) | None |
| `POST` | [`/generate_executive_summary`](#4-generate-executive-summary) | Generate executive summary on demand | None |
| `POST` | [`/generate_probing_questions`](#5-generate-probing-questions) | Generate scored probing questions | None |
| `POST` | [`/autofill_persona`](#6-autofill-persona) | Crawl website → auto-fill persona + ingest KB | None |
| `POST` | [`/generate_instructions`](#7-generate-instructions) | Generate probing instruction suggestions | None |
| `POST` | [`/generate_templates`](#8-generate-templates) | Generate WhatsApp message templates | None |
| `GET` | [`/cache_stats`](#9-cache-stats) | Prompt cache statistics | None |
| `POST` | [`/cache_stats/reset`](#10-reset-cache-stats) | Reset prompt cache statistics | None |

---

## 1. Health Check

```
GET /health
```

Simple liveness probe. Returns immediately with no external dependencies checked.

**Response:**
```json
{
  "status": "healthy"
}
```

**Status codes:** `200 OK`

**curl:**
```bash
curl http://localhost:8000/health
```

---

## 2. Chat (Production)

```
POST /chat
```

The primary chat endpoint for production integrations. Processes a user message through the multi-agent system and returns a structured `APIResponse`.

### Request Body — `BotRequest`

```json
{
  "user_context": {
    "user_id": "user_123",
    "tenant_id": "tenant_abc",
    "user_query": "I want to book a demo",
    "message_id": "msg_uuid_optional",
    "chat_history": [],
    "contact_details": null,
    "timezone": "Asia/Kolkata",
    "region_code": "IN",
    "proceed_email_details": null
  },
  "bot_persona": null
}
```

#### `user_context` Fields (UserContextRequest)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | `string` | Recommended | Unique user identifier. If null, a session may not persist correctly. |
| `tenant_id` | `string` | Recommended | Tenant/organization identifier. Used for multi-tenant isolation (KB collections, sessions). |
| `user_query` | `string` | **Yes** | The user's message text. |
| `message_id` | `string` | No | Client-provided unique ID for this turn. Auto-generated (UUID) if omitted. |
| `chat_history` | `array` | No | Previous conversation turns. Format: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`. If null, loaded from session. |
| `contact_details` | `ContactDetails` | No | Pre-known contact info (name, email, phone, company). See [ContactDetails](#contactdetails). |
| `timezone` | `string` | No | IANA timezone string (e.g., `"Asia/Kolkata"`, `"America/New_York"`). Resolved from `region_code` if not provided. |
| `region_code` | `string` | No | ISO 3166-1 alpha-2 country code (e.g., `"IN"`, `"US"`). Used to resolve timezone. |
| `proceed_email_details` | `ProceedEmailDetails` | No | Pre-existing email handoff state. Typically null on first request. |

#### `bot_persona` (Optional)

Full `BotPersona` object to override the stored persona. If null, the persona from the existing session is used. See [PERSONA_GUIDE.md](PERSONA_GUIDE.md) for the complete schema.

### Response Body — `APIResponse`

```json
{
  "response": "I'd be happy to help you book a demo! Could you share your email address?",
  "user_id": "user_123",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "tenant_abc",
  "chat_history": [
    {"role": "user", "content": "I want to book a demo"},
    {"role": "assistant", "content": "I'd be happy to help..."}
  ],
  "chat_summary": "User wants to book a demo. Bot is collecting details.",
  "executive_summary": null,
  "contact_details": null,
  "lead_details": null,
  "follow_trigger": false,
  "ask_new_date": false,
  "timezone": "Asia/Kolkata",
  "region_code": "IN",
  "collected_fields": {},
  "all_info_collected": false,
  "booking_confirmed": false,
  "booking_type": "new",
  "new_booking": true,
  "last_agent": "demo_booking_agent",
  "followup_details": null,
  "consumption_info": {
    "total_input_tokens": 1250,
    "total_output_tokens": 85,
    "total_reasoning_tokens": 0,
    "total_cached_tokens": 800,
    "turn_details": [...]
  },
  "brochure_flag": false,
  "asset_shared_details": null
}
```

#### APIResponse Fields

| Field | Type | Description |
|-------|------|-------------|
| `response` | `string` | The bot's reply text. Always present (may be fallback on error). |
| `user_id` | `string?` | Echo of the user identifier. |
| `message_id` | `string` | Unique message ID for this turn (UUID). |
| `tenant_id` | `string?` | Echo of the tenant identifier. |
| `chat_history` | `array?` | Updated conversation history including the current turn. |
| `chat_summary` | `string?` | Rolling summary of the conversation (generated by summarizer). |
| `executive_summary` | `string?` | Executive summary if generated. |
| `contact_details` | `ContactDetails?` | Collected contact details (name, email, phone, company). |
| `lead_details` | `LeadAnalysis?` | Lead classification result (after booking confirmation). |
| `follow_trigger` | `boolean` | `true` if a follow-up reminder was scheduled. |
| `ask_new_date` | `boolean` | `true` if the bot needs the user to suggest a different date/time. |
| `timezone` | `string?` | Resolved IANA timezone. |
| `region_code` | `string?` | Resolved country code. |
| `collected_fields` | `object?` | Fields collected during booking (email, date, time, products, etc.). |
| `all_info_collected` | `boolean` | `true` when all mandatory booking fields are collected. |
| `booking_confirmed` | `boolean` | `true` when a booking is successfully confirmed via Calendly. |
| `booking_type` | `string?` | One of: `"new"`, `"reschedule"`, `"cancel"`. |
| `new_booking` | `boolean` | `true` when a new booking flow was initiated this session. |
| `last_agent` | `string?` | Name of the last agent that handled the request (e.g., `"sales_agent"`, `"demo_booking_agent"`). |
| `followup_details` | `FollowupDetails?` | Follow-up scheduling details. |
| `consumption_info` | `ConsumptionInfo?` | LLM token consumption breakdown for this turn. |
| `brochure_flag` | `boolean` | `true` if an asset/brochure was shared this turn. |
| `asset_shared_details` | `AssetSharedDetails?` | Details of the shared asset (id, name, path). |

### Error Handling

On unhandled exceptions, `/chat` returns a **200 OK** with a fallback response (not a 500):

```json
{
  "response": "I apologize, but I encountered an issue processing your request. Please try again or rephrase your question.",
  "user_id": "user_123"
}
```

This design ensures the frontend always receives a displayable message.

### curl Example

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_context": {
      "user_id": "user_001",
      "tenant_id": "tenant_001",
      "user_query": "Hi, tell me about your products"
    }
  }'
```

### Minimal Request (All Defaults)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_context": {
      "user_query": "Hello"
    }
  }'
```

---

## 3. Chat UI (Streamlit)

```
POST /chat_ui
```

Identical to `/chat` in processing, but returns the **full `BotState`** as a dictionary instead of the curated `APIResponse`. Used by the Streamlit admin panel for debugging and full state inspection.

### Request Body

Same as [`/chat`](#2-chat-production) — accepts `BotRequest`.

### Response Body

Returns a dictionary representation of the entire `BotState` Pydantic model, which includes:

- All fields from `APIResponse`
- Internal agent state (`probing_context`, `objection_state`, `negotiation_state`)
- Full `bot_persona` configuration
- Guardrail decisions (`input_guardrail_decision`, `output_guardrail_decision`)
- Internal flags (`human_requested`, `escalation_timestamp`, `brochure_details`, etc.)
- Raw `agent_result` from the agent execution

### curl Example

```bash
curl -X POST http://localhost:8000/chat_ui \
  -H "Content-Type: application/json" \
  -d '{
    "user_context": {
      "user_id": "user_debug",
      "tenant_id": "tenant_dev",
      "user_query": "Show me your pricing"
    }
  }'
```

**Status codes:** `200 OK` or `500 Internal Server Error` (with detail message).

> **Note:** Unlike `/chat`, this endpoint does NOT return a graceful fallback on error — it raises an HTTP 500 exception. This is intentional for debugging purposes.

---

## 4. Generate Executive Summary

```
POST /generate_executive_summary
```

Standalone endpoint to generate a structured executive summary of a conversation. Uses the summarizer LLM model (`gpt-4.1-nano`).

### Request Body — `ExecutiveSummaryRequest`

```json
{
  "agent_result": [
    {"role": "user", "content": "I want to learn about your products"},
    {"role": "assistant", "content": "We offer several solutions..."}
  ],
  "chat_history": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_result` | `array` | No (but recommended) | Raw agent execution result — primary input for summary generation. |
| `chat_history` | `array` | No | Fallback input if `agent_result` is empty. Same format as chat history. |

### Response

```json
{
  "executive_summary": "## Executive Summary\n\nThe prospect expressed interest in healthcare solutions..."
}
```

### curl Example

```bash
curl -X POST http://localhost:8000/generate_executive_summary \
  -H "Content-Type: application/json" \
  -d '{
    "agent_result": [
      {"role": "user", "content": "Tell me about your patient management system"},
      {"role": "assistant", "content": "Our Patient Management System helps..."}
    ]
  }'
```

**Status codes:** `200 OK` or `500 Internal Server Error`.

---

## 5. Generate Probing Questions

```
POST /generate_probing_questions
```

Generates scored, prioritized probing questions tailored to a bot persona. Used during persona setup to create the question set for lead qualification.

### Request Body — `ProbingRequest`

```json
{
  "custom_persona": {
    "company_name": "AI Sante",
    "industry": "Healthcare Technology",
    "products": [
      {"product_name": "Patient Management System", "description": "..."}
    ]
  },
  "total_k": 5,
  "comment": "Focus on budget and timeline questions"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `custom_persona` | `object` | No | `null` | Partial or full `BotPersona` dict. If null, uses defaults. |
| `total_k` | `integer` | No | `5` | Number of probing questions to generate. |
| `comment` | `string` | No | `""` | Additional instructions for question generation. |

### Response — `ProbingAgentResponse`

```json
{
  "questions": [
    {
      "id": "pq_001",
      "question": "What is the size of your medical team?",
      "score": 15.0,
      "priority": 1,
      "mandatory": true
    },
    {
      "id": "pq_002",
      "question": "What tools do you currently use for patient records?",
      "score": 20.0,
      "priority": 2,
      "mandatory": true
    }
  ],
  "total_k_generated": 5
}
```

### curl Example

```bash
curl -X POST http://localhost:8000/generate_probing_questions \
  -H "Content-Type: application/json" \
  -d '{
    "custom_persona": {
      "company_name": "MedTech Corp",
      "industry": "Healthcare"
    },
    "total_k": 3
  }'
```

---

## 6. Autofill Persona

```
POST /autofill_persona
```

Crawls a website using Crawl4AI, extracts company information, and auto-generates a `BotPersona`. Also ingests the crawled content into the tenant's Qdrant knowledge base collection.

### Request Body — `AutofillPersonaRequest`

```json
{
  "user_id": "user_001",
  "url": "https://example-company.com",
  "tenant_id": "tenant_001",
  "max_depth": 2,
  "max_pages": 50,
  "max_tokens": 30000,
  "max_products": 5
}
```

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `user_id` | `string` | **Yes** | — | — | User ID for session and KB ingestion. |
| `url` | `string` | **Yes** | — | Valid URL | Website URL to crawl. |
| `tenant_id` | `string` | No | `null` | — | Tenant ID for VectorDB collection. Falls back to session tenant_id. |
| `max_depth` | `integer` | No | `2` | 1–5 | Maximum crawl depth from the root URL. |
| `max_pages` | `integer` | No | `50` | 10–100 | Maximum number of pages to crawl. |
| `max_tokens` | `integer` | No | `30000` | 10000–50000 | Maximum tokens to send to LLM for persona generation. |
| `max_products` | `integer` | No | `5` | 1–100 | Maximum products to extract from the website. |

### Response

```json
{
  "pages_analyzed": 12,
  "urls": [
    "https://example-company.com",
    "https://example-company.com/products",
    "https://example-company.com/about"
  ],
  "bot_persona": {
    "name": "Alex",
    "company_name": "Example Corp",
    "industry": "Technology",
    "products": [...],
    "target_audience": "Enterprise B2B",
    ...
  }
}
```

### curl Example

```bash
curl -X POST http://localhost:8000/autofill_persona \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_setup",
    "url": "https://example-company.com",
    "tenant_id": "tenant_001",
    "max_depth": 2,
    "max_pages": 30
  }'
```

**Status codes:** `200 OK` or `500 Internal Server Error`.

> **Note:** This endpoint performs web crawling and LLM processing. Response time can be 30–120 seconds depending on website size and crawl parameters.

---

## 7. Generate Instructions

```
POST /generate_instructions
```

Generates probing instruction text suggestions based on a persona. These instructions guide how the bot should approach probing conversations.

### Request Body — `InstructionAgentRequest`

```json
{
  "custom_persona": {
    "company_name": "AI Sante",
    "industry": "Healthcare",
    "products": [...]
  },
  "max_instructions": 5
}
```

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `custom_persona` | `object` | No | `null` | — | Partial or full `BotPersona` dict. |
| `max_instructions` | `integer` | No | `5` | 1–10 | Maximum number of instructions to generate. |

### Response — `InstructionAgentResponse`

```json
{
  "instructions": [
    "Ask about team size to understand scale requirements",
    "Identify current pain points with existing tools",
    "Determine budget range and procurement timeline",
    "Assess technical infrastructure and integration needs",
    "Gauge decision-making authority and stakeholders"
  ]
}
```

### curl Example

```bash
curl -X POST http://localhost:8000/generate_instructions \
  -H "Content-Type: application/json" \
  -d '{
    "custom_persona": {
      "company_name": "TechStart",
      "industry": "SaaS"
    },
    "max_instructions": 3
  }'
```

---

## 8. Generate Templates

```
POST /generate_templates
```

Generates WhatsApp message templates for each product in the persona. Returns structured template objects compatible with WhatsApp Business API.

### Request Body — `TemplateGenerationRequest`

```json
{
  "custom_persona": {
    "company_name": "AI Sante",
    "products": [
      {"product_name": "Patient Management System", "description": "..."},
      {"product_name": "Telemedicine Platform", "description": "..."}
    ]
  },
  "max_products": 5
}
```

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `custom_persona` | `object` | No | `null` | — | Partial or full `BotPersona` dict. |
| `max_products` | `integer` | No | `5` | 1–20 | Maximum products to generate templates for. |

### Response — `TemplateGenerationResponse`

```json
{
  "templates": [
    {
      "name": "patient_mgmt_intro",
      "category": "Marketing",
      "language": "English",
      "header_type": "Text",
      "body": "Hi {{1}}! 👋 Discover how AI Sante's Patient Management System can streamline your clinic operations. Our solution helps manage patient records, appointments, and billing — all in one place.",
      "variables": ["Customer Name"],
      "footer": "To OPT Out, type STOP",
      "buttons": [
        {
          "button_type": "Url",
          "button_text": "Learn More"
        }
      ]
    }
  ],
  "total_templates": 2
}
```

#### WhatsAppTemplate Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Template name (snake_case). |
| `category` | `string` | `"Marketing"` or `"Utility"`. |
| `language` | `string` | Template language (e.g., `"English"`). |
| `header_type` | `string` | `"Text"`, `"Image"`, `"Video"`, or `"Document"`. |
| `body` | `string` | Message body with `{{1}}`, `{{2}}` variable placeholders. |
| `variables` | `array?` | Human-readable names for each variable placeholder. |
| `footer` | `string?` | Footer text. Default: `"To OPT Out, type STOP"`. |
| `buttons` | `array?` | List of `TemplateButton` objects with `button_type` and `button_text`. |

### curl Example

```bash
curl -X POST http://localhost:8000/generate_templates \
  -H "Content-Type: application/json" \
  -d '{
    "custom_persona": {
      "company_name": "AI Sante",
      "products": [
        {"product_name": "Telemedicine Platform"}
      ]
    },
    "max_products": 3
  }'
```

---

## 9. Cache Stats

```
GET /cache_stats
```

Returns prompt cache statistics from OpenAI's automatic prompt prefix caching.

### Response

```json
{
  "total_requests": 150,
  "cache_hits": 92,
  "cache_misses": 58,
  "hit_rate": 0.613,
  "total_cached_tokens": 125000,
  "total_input_tokens": 200000,
  "token_cache_rate": 0.625,
  "estimated_cost_savings_percent": 31.25
}
```

### curl Example

```bash
curl http://localhost:8000/cache_stats
```

---

## 10. Reset Cache Stats

```
POST /cache_stats/reset
```

Resets the prompt cache statistics counters to zero.

### Response

```json
{
  "status": "reset",
  "message": "Cache statistics have been reset"
}
```

### curl Example

```bash
curl -X POST http://localhost:8000/cache_stats/reset
```

---

## Data Models Reference

### ContactDetails

```json
{
  "name": "John Doe",
  "email": "john@company.com",
  "phone": "+91-9876543210",
  "company_name": "Acme Corp"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string?` | Contact person name |
| `email` | `string?` | Email address (validated for format and common typos) |
| `phone` | `string?` | Phone number |
| `company_name` | `string?` | Company/organization name |

### LeadAnalysis

Returned in `lead_details` after a booking is confirmed.

```json
{
  "lead_classification": "hot",
  "reasoning": "User showed strong intent, discussed budget, and booked a demo within the first conversation.",
  "key_indicators": ["direct demo request", "budget discussed", "timeline: Q2"],
  "recommended_next_action": "Priority follow-up within 24 hours",
  "urgency_level": "immediate"
}
```

| Field | Type | Values |
|-------|------|--------|
| `lead_classification` | `string` | `"hot"`, `"warm"`, `"cold"` |
| `reasoning` | `string` | Detailed analysis text |
| `key_indicators` | `array` | List of indicator strings |
| `recommended_next_action` | `string` | Suggested follow-up action |
| `urgency_level` | `string` | `"immediate"`, `"soon"`, `"later"`, `"no-interest"` |

### FollowupDetails

Returned in `followup_details` when a follow-up is scheduled.

```json
{
  "followup_flag": true,
  "followup_time": "2026-03-07T10:00:00Z",
  "followup_type": "reminder",
  "timezone_confirmed": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `followup_flag` | `boolean` | `true` when a follow-up is active |
| `followup_time` | `string` | UTC ISO 8601 timestamp for the follow-up |
| `followup_type` | `string?` | Type of follow-up (e.g., `"reminder"`) |
| `timezone_confirmed` | `boolean` | Whether timezone was confirmed with the user |

### AssetSharedDetails

Returned in `asset_shared_details` when `brochure_flag` is `true`.

```json
{
  "asset_id": "asset_001",
  "asset_name": "Product Catalog 2026",
  "asset_path": "https://cdn.example.com/catalog.pdf"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `asset_id` | `string` | Unique asset identifier from persona |
| `asset_name` | `string` | Display name of the asset |
| `asset_path` | `string` | Download URL or file path |

### ConsumptionInfo

Token consumption breakdown for the current turn.

```json
{
  "total_input_tokens": 1250,
  "total_output_tokens": 85,
  "total_reasoning_tokens": 0,
  "total_cached_tokens": 800,
  "turn_details": [
    {
      "model": "azure/gpt-5.1-chat",
      "input_tokens": 1100,
      "output_tokens": 75,
      "reasoning_tokens": 0,
      "cached_tokens": 800
    },
    {
      "model": "azure/gpt-4.1-nano",
      "input_tokens": 150,
      "output_tokens": 10,
      "reasoning_tokens": 0,
      "cached_tokens": 0
    }
  ]
}
```

---

## Error Handling

### `/chat` Endpoint

The `/chat` endpoint is designed to **never return HTTP errors** to the client. On any unhandled exception, it returns a `200 OK` with a friendly fallback message:

```json
{
  "response": "I apologize, but I encountered an issue processing your request. Please try again or rephrase your question.",
  "user_id": "<from request>"
}
```

### Other Endpoints

All other POST endpoints return standard HTTP error codes:

| Code | Meaning | When |
|------|---------|------|
| `200` | Success | Request processed successfully |
| `422` | Validation Error | Request body fails Pydantic validation |
| `500` | Internal Server Error | Unhandled exception during processing |

### 422 Validation Error Format (FastAPI Default)

```json
{
  "detail": [
    {
      "loc": ["body", "user_context", "user_query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### LLM Provider Fallback

LLM failures are handled transparently via the LiteLLM Router's fallback chain:

1. **Primary:** `azure/gpt-5.1-chat`
2. **Fallback 1:** `openai/gpt-5.1`
3. **Fallback 2:** `gemini/gemini-3-flash`

If all providers fail, the error propagates to the endpoint's error handler.

---

## Rate Limits & Performance

### Response Time Expectations

| Endpoint | Typical Response Time | Notes |
|----------|----------------------|-------|
| `/health` | < 10ms | No external calls |
| `/chat` | 2–8 seconds | Depends on agent chain length and LLM latency |
| `/chat_ui` | 2–8 seconds | Same as `/chat` |
| `/generate_executive_summary` | 3–10 seconds | Single LLM call |
| `/generate_probing_questions` | 5–15 seconds | Single LLM call |
| `/autofill_persona` | 30–120 seconds | Web crawling + LLM processing |
| `/generate_instructions` | 3–10 seconds | Single LLM call |
| `/generate_templates` | 5–20 seconds | Depends on product count |
| `/cache_stats` | < 10ms | In-memory stats |

### Semantic Cache (Per-Session)

- Similar queries (cosine similarity > 0.5) return cached responses without LLM calls
- Cache: per `user_id`, max 15 entries (FIFO eviction)
- Embeddings: Azure OpenAI embedding model

### Prompt Caching

- OpenAI's built-in prompt prefix caching is leveraged when `ENABLE_PROMPT_CACHING=true`
- System/developer messages are split to maximize cache hits across turns
- Cache hit rate visible via `/cache_stats`

### Concurrency

- FastAPI runs with `asyncio` — all endpoints are `async`
- Agent execution is async via the OpenAI Agents SDK `Runner.run()`
- Database operations use SQLAlchemy async sessions (production PostgreSQL)
- No built-in rate limiting — add via middleware/reverse proxy (e.g., nginx, API Gateway)
