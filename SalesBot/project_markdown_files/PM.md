# BotRunner — Product Manager Reference

> **Last Updated:** March 6, 2026 &nbsp;|&nbsp; **Version:** 2.1.0  
> **Audience:** Product Managers, Business Stakeholders

---

## Table of Contents

- [Product Overview](#product-overview)
- [Capability Summary](#capability-summary)
- [Feature Inventory](#feature-inventory)
  - [Core Chat Features](#core-chat-features)
  - [Sales & Product Discovery](#sales--product-discovery)
  - [Demo Booking System](#demo-booking-system)
  - [Lead Qualification (Probing)](#lead-qualification-probing)
  - [Pricing & Negotiation](#pricing--negotiation)
  - [Follow-up Scheduling](#follow-up-scheduling)
  - [Human Escalation](#human-escalation)
  - [Email Handoff](#email-handoff)
  - [Asset/Document Sharing](#assetdocument-sharing)
  - [Persona System](#persona-system)
  - [Admin & Tooling](#admin--tooling)
  - [Infrastructure Features](#infrastructure-features)
- [Known Limitations](#known-limitations)
- [Configuration Surface Area](#configuration-surface-area)
- [Metrics & Observability](#metrics--observability)
- [Roadmap Considerations](#roadmap-considerations)

---

## Product Overview

BotRunner is an **AI-powered sales assistant platform** that automates the early stages of sales conversations. It handles product discovery, lead qualification, demo scheduling, pricing discussions, and human escalation — all through natural multi-turn conversation.

**Target user:** B2B companies with products/services that require consultative sales.

**Key value proposition:**
- Automates 80%+ of first-touch sales conversations
- Qualifies leads before they reach human sales reps
- Books demos directly integrated with Calendly
- Handles pricing negotiation within defined guardrails
- Operates 24/7 in the user's language

---

## Capability Summary

| Capability | Status | Notes |
|-----------|--------|-------|
| Multi-turn conversation | ✅ Live | Stateful sessions with full history |
| Product/feature Q&A from knowledge base | ✅ Live | RAG-powered from Qdrant/ChromaDB |
| Demo booking (new/reschedule/cancel) | ✅ Live | Calendly integration |
| Lead qualification via scored probing | ✅ Live | Configurable questions, scores, thresholds |
| Pricing negotiation with discount limits | ✅ Live | Protected discount caps, multi-turn |
| Follow-up reminder scheduling | ✅ Live | Timezone-aware, relative/absolute parsing |
| Human escalation with context handoff | ✅ Live | Summary, sentiment, contact details |
| Email channel switch | ✅ Live | Template matching, HTML generation |
| Asset/document sharing | ✅ Live | Brochures, PDFs, datasheets |
| Website crawl → auto-configure persona | ✅ Live | Crawl4AI + LLM extraction |
| WhatsApp template generation | ✅ Live | Per-product templates |
| Multi-language support | ✅ Live | Auto-detect language + respond in kind |
| Input guardrail (attack detection) | ✅ Live | Record-only (doesn't block users) |
| Output guardrail (quality control) | ✅ Live | 12 validation rules, can replace bad responses |
| Prompt caching optimization | ✅ Live | Reduces LLM costs via prefix caching |
| Semantic response caching | ✅ Live | Deduplicates similar queries per session |
| LLM provider failover | ✅ Live | Azure → OpenAI → Gemini |
| Observability & cost tracking | ✅ Live | Opik tracing, per-turn token breakdown |

---

## Feature Inventory

### Core Chat Features

| Feature | Description | Configurable? |
|---------|-------------|---------------|
| **Session persistence** | Each user+tenant has a persistent session across messages | Automatic |
| **Conversation history** | Rolling history with configurable max (default 15 messages) | `MAX_HISTORY` env var |
| **Activity Summary** | Generated when the Lead is generated | Automatic |
| **Executive summary** | Generated Explicitly | Explicit |
| **Multi-tenant isolation** | Sessions, knowledge base, and data isolated per tenant_id | Automatic |
| **Language detection** | Detects user language and script, responds accordingly | Automatic |
| **Semantic cache** | Avoids redundant LLM calls for similar queries | Per-session, 15 entries |

### Sales & Product Discovery

| Feature | Description | Configurable? |
|---------|-------------|---------------|
| **Knowledge base Q&A** | Answers product questions from ingested documents | Tenant KB (Qdrant) |
| **RAG retrieval** | Hybrid search + cross-encoder reranking | RAG pipeline config |
| **Sales personality** | Bot maintains configured personality during conversations | `persona.personality` |
| **Objection handling** | Classifies objections (soft/hard/hidden) and responds empathetically | Built-in |
| **Product catalog** | Multi-product support with per-product details | `persona.products[]` |

### Demo Booking System

| Feature | Description | Configurable? |
|---------|-------------|---------------|
| **New booking** | Collects email, date/time, products → books via Calendly | Working hours config |
| **Reschedule** | Changes existing booking time | Automatic |
| **Cancel** | Cancels existing booking | Automatic |
| **Natural date parsing** | "next Tuesday at 3 PM", "in 2 days", "morning" | Built-in |
| **Timezone resolution** | Auto-resolves from country code | `region_code` in request |
| **Working hours validation** | Rejects weekends, holidays, outside business hours | `persona.working_hours[]` |
| **Calendly availability** | Real-time slot checking against Calendly | Calendly API config |
| **Alternative slot suggestions** | Suggests available alternatives when slot unavailable | Automatic |
| **Lead classification** | Classifies lead as hot/warm/cold after booking | Automatic |
| **Email validation** | Validates format + detects common typos (gmail vs gmial) | Built-in |

### Lead Qualification (Probing)

| Feature | Description | Configurable? |
|---------|-------------|---------------|
| **Scored probing questions** | Each question has a score; total tracked per user | `persona.probing_questions[]` |
| **Priority ordering** | Questions asked in priority order (lowest first) | `question.priority` |
| **Mandatory questions** | Must be asked before optional at same priority | `question.mandatory` |
| **Score threshold** | CTA shown when cumulative score reaches threshold | `persona.probing_threshold` (default: 50) |
| **CTA trigger** | Configurable call-to-action (e.g., "Book a Demo") | `persona.current_cta` |
| **Objection handling** | Counts objections; triggers CTA at limit | `persona.objection_count_limit` (default: 3) |
| **Reset cycle** | After objection limit, resets and tries again | `persona.reset_count_limit` (default: 2) |
| **Freeze protection** | After max resets, stops probing pressure entirely | Automatic |
| **Enable/disable** | Master switch for the probing system | `persona.enable_probing` |

### Pricing & Negotiation

| Feature | Description | Configurable? |
|---------|-------------|---------------|
| **Per-product pricing** | Each product has its own base price | `product.base_price` |
| **Discount negotiation** | Multi-turn pricing discussion within limits | `product.max_discount_percent` or `persona.negotiation_config` |
| **Protected pricing** | Base price and max discount cannot be overridden by AI | System-enforced |
| **Budget awareness** | Detects user budget constraints and adjusts offers | Automatic |
| **Currency support** | Configurable currency display | `negotiation_config.currency` |
| **Discount lock** | Final offer locks the discount, preventing further changes | Automatic |

### Follow-up Scheduling

| Feature | Description | Configurable? |
|---------|-------------|---------------|
| **Relative scheduling** | "in 30 minutes", "in 2 hours", "tomorrow" | Built-in |
| **Absolute scheduling** | "March 15th at 2 PM", "next Monday" | Built-in |
| **Hindi number support** | "do ghante baad" (in 2 hours) | Built-in |
| **Timezone confirmation** | Resolves and confirms user timezone | Automatic |
| **90-day maximum** | Follow-ups limited to 90 days in the future | Hardcoded |

### Human Escalation

| Feature | Description | Configurable? |
|---------|-------------|---------------|
| **Conversation summary** | Generates summary for human agent | Automatic |
| **Topic extraction** | Lists key topics discussed | Automatic |
| **Sentiment analysis** | Classifies user sentiment for handoff | Automatic |
| **Email collection** | Collects and validates email for follow-up | Automatic |
| **Ready-for-handoff flag** | Signals when preparation is complete | `human_details.ready_for_handoff` |

### Email Handoff

| Feature | Description | Configurable? |
|---------|-------------|---------------|
| **Template matching** | Matches conversation to email templates | `persona.email_template[]` |
| **HTML email generation** | Generates formatted email body | Automatic |
| **Email collection** | If no email on file, asks user | Automatic |

### Asset/Document Sharing

| Feature | Description | Configurable? |
|---------|-------------|---------------|
| **Asset matching** | Matches user request to available assets | `persona.assets[]` |
| **Multi-asset selection** | Presents options when multiple match | Automatic |
| **Asset listing** | Lists all available assets when none match | Automatic |

### Persona System

| Feature | Description | Configurable? |
|---------|-------------|---------------|
| **Full persona configuration** | Name, company, industry, personality, tone, products, rules | See [PERSONA_GUIDE.md](PERSONA_GUIDE.md) |
| **Website auto-fill** | Crawl website → generate persona automatically | `/autofill_persona` endpoint |
| **Probing question generation** | AI generates scored questions for a persona | `/generate_probing_questions` endpoint |
| **Instruction generation** | AI generates probing instructions | `/generate_instructions` endpoint |
| **Template generation** | AI generates WhatsApp templates per product | `/generate_templates` endpoint |
| **Working hours** | Per-day schedule with holiday support | `persona.working_hours[]` |
| **Custom rules** | Persona-specific behavioral rules | `persona.rules[]` |
| **Multi-product support** | Unlimited products with descriptions and pricing | `persona.products[]` |

### Admin & Tooling

| Feature | Description | Access |
|---------|-------------|--------|
| **Streamlit admin panel** | Visual UI for chat testing, persona editing, QA | `streamlit_ui/app.py` |
| **Interactive API docs** | Auto-generated Swagger UI and ReDoc | `/docs`, `/redoc` |
| **Cache statistics** | Monitor prompt cache hit rates and savings | `/cache_stats` |

### Infrastructure Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Multi-provider LLM failover** | Azure → OpenAI → Gemini automatic fallback | ✅ Live |
| **Prompt prefix caching** | Optimizes costs by caching static system prompts | ✅ Live |
| **Semantic response caching** | Avoids redundant LLM calls for similar queries | ✅ Live |
| **Token consumption tracking** | Per-turn breakdown (input, output, cached, reasoning) | ✅ Live |
| **Opik observability** | Full LLM call tracing with cost tracking | ✅ Live |
| **Async execution** | Non-blocking I/O throughout the stack | ✅ Live |
| **SQLite/PostgreSQL flexibility** | SQLite for dev, Neon PG for production | ✅ Live |

---

## Known Limitations

### Functional Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| **Single conversation thread per user** | Users can't have parallel conversations | Use different `user_id` values |
| **No voice/audio support** | Text-only conversations | Integrate with STT/TTS externally |
| **No image/file upload from users** | Can't analyze user-uploaded files | Planned for future |
| **No real-time Calendly webhook** | Availability checked at time of request, not live-pushed | Polling at booking time |
| **Probing is sequential** | Questions asked one at a time, not batched | By design for natural conversation |
| **Discount negotiation is per-product** | Can't negotiate bundle discounts across products | Enhancement opportunity |
| **No A/B testing built-in** | Can't test persona variations natively | Use different persona configs |
| **90-day follow-up limit** | Can't schedule follow-ups beyond 90 days | Hardcoded limit |

### Technical Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| **SQLite concurrency in dev** | Concurrent requests may conflict in dev mode | Use PostgreSQL for load testing |
| **No built-in rate limiting** | Must add via middleware or reverse proxy | nginx/API Gateway recommended |
| **No authentication/authorization** | API endpoints are unprotected by default | Add auth middleware |
| **In-memory semantic cache** | Cache lost on server restart | Acceptable for per-session caching |
| **Guardrail adds latency** | ~0.5–1s additional per turn (nano model) | GPT-4.1-nano is fast; acceptable tradeoff |
| **Cold start latency** | First request: 5–15s (model loading, connections) | Warm up in deployment |

---

## Configuration Surface Area

Summary of everything that can be configured without code changes:

### Via Environment Variables (`.env`)

- LLM model selection (primary, guardrail, summarizer, fallbacks)
- Database type and connection
- RAG vector database connection
- Conversation history limits
- Prompt caching toggle
- Observability settings

### Via BotPersona (per-tenant, runtime)

- Bot name, company, industry
- Personality and communication tone
- Products catalog with pricing
- Assets and documents
- Working hours and holidays
- Probing questions with scores and priorities
- Probing threshold and CTA
- Objection handling limits
- Negotiation config (currency, max discounts)
- Email templates
- Custom behavioral rules
- Target audience and company description

### Via API Request (per-message)

- User identity (`user_id`, `tenant_id`)
- Pre-known contact details
- Chat history override
- Timezone and region
- Email details
- Full persona override

---

## Metrics & Observability

### Available Metrics

| Metric | Source | Description |
|--------|--------|-------------|
| **Token consumption** | `consumption_info` in APIResponse | Per-turn input/output/cached/reasoning tokens |
| **Cache hit rate** | `/cache_stats` endpoint | Prompt prefix cache statistics |
| **Agent routing** | `last_agent` in APIResponse | Which agent handled each turn |
| **Lead classification** | `lead_details` in APIResponse | Hot/warm/cold after booking |
| **Booking conversion** | `booking_confirmed` flag | Whether a demo was booked |
| **Follow-up scheduling** | `follow_trigger` flag | Whether a follow-up was set |
| **Human escalation rate** | `human_requested` flag | How often users escalate |
| **LLM traces** | Opik dashboard | Full execution traces with latency/cost |

### Key Business Metrics (Derivable)

- **Conversation-to-booking rate** = bookings / total conversations
- **Probing completion rate** = score threshold reached / probing sessions
- **Average turns to booking** = total turns / bookings
- **Escalation rate** = human escalations / total conversations
- **Average discount given** = mean `current_discount_percent` across sessions

---

## Roadmap Considerations

### High-Impact Opportunities

| Opportunity | Description | Complexity |
|-------------|-------------|------------|
| **Multi-channel integration** | WhatsApp, Slack, Teams connectors | Medium |
| **Voice support** | STT/TTS integration for phone bots | High |
| **A/B persona testing** | Built-in variant testing for personas and prompts | Medium |
| **Bundle negotiation** | Cross-product discount negotiation | Medium |
| **Analytics dashboard** | Built-in metrics visualization | Medium |
| **Webhook integrations** | CRM (Salesforce, HubSpot) data push on events | Medium |
| **Multi-thread support** | Parallel conversation threads per user | Low |
| **User file upload** | Accept and analyze documents from users | Medium |
| **Scheduled campaigns** | Automated outbound message sequences | High |
