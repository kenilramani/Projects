# BotRunner Persona Configuration Guide

> **Last Updated:** March 6, 2026 &nbsp;|&nbsp; **Version:** 2.1.0  
> **Audience:** Developers, Solution Engineers, Customer Success

---

## Table of Contents

- [What Is a Persona?](#what-is-a-persona)
- [How to Set a Persona](#how-to-set-a-persona)
- [Complete Field Reference](#complete-field-reference)
  - [Identity Fields](#identity-fields)
  - [Company Fields](#company-fields)
  - [Product Catalog](#product-catalog)
  - [Behavioral Settings](#behavioral-settings)
  - [Probing Configuration](#probing-configuration)
  - [Negotiation Configuration](#negotiation-configuration)
  - [Working Hours](#working-hours)
  - [Assets](#assets)
  - [Email Templates](#email-templates)
  - [Management Contacts](#management-contacts)
- [How Persona Affects Bot Behavior](#how-persona-affects-bot-behavior)
- [Auto-Setup via Website Crawl](#auto-setup-via-website-crawl)
- [Example Configurations](#example-configurations)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## What Is a Persona?

A **persona** is the complete configuration that defines who the bot is and how it behaves. It is represented by the `BotPersona` Pydantic model in `app/core/models.py` and is passed in every API request via the `bot_persona` field of `BotRequest`.

The persona controls:

| Area | What It Determines |
|------|--------------------|
| **Identity** | Bot name, company, industry |
| **Knowledge** | Product catalog, features, USPs |
| **Personality** | Tone, emoji usage, name usage |
| **Rules** | Hard constraints on bot behavior |
| **Lead qualification** | Probing questions, thresholds, CTA |
| **Negotiation** | Discount caps, currency |
| **Scheduling** | Working hours for demo booking |
| **Assets** | Brochures, documents available to share |
| **Email** | Templates for email handoff |

Every conversation uses the persona to dynamically generate agent instructions at runtime via `app/instructions/generators.py`. Changing the persona changes bot behavior instantly for new conversations.

---

## How to Set a Persona

### Option 1: API Request (Manual)

Pass the `bot_persona` object in the `BotRequest` body to `/chat` or `/chat_ui`:

```json
{
  "bot_persona": {
    "name": "Aria",
    "company_name": "Acme Corp",
    "industry": "SaaS",
    "personality": "Professional, warm, consultative",
    "company_products": [ ... ],
    "rules": [ ... ],
    ...
  },
  "user_context": { ... }
}
```

### Option 2: Website Auto-Setup

Call the `/autofill_persona` endpoint with a URL:

```json
{
  "url": "https://www.example.com",
  "user_id": "user_123",
  "tenant_id": "tenant_456",
  "max_depth": 2,
  "max_pages": 50,
  "max_products": 5
}
```

The system crawls the website, extracts company information, and returns a fully populated `BotPersona`. See [Auto-Setup via Website Crawl](#auto-setup-via-website-crawl).

### Option 3: Streamlit Admin Panel

The Streamlit UI (`streamlit_ui/persona.py`) provides a form-based interface for building and editing personas interactively.

---

## Complete Field Reference

### Identity Fields

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `name` | `string` | `""` | Yes | Bot's display name. Used in greetings and self-references. |
| `personality` | `string` | `null` | No | Personality description. Directly injected into system prompt. Examples: `"Professional and empathetic"`, `"Casual and witty"`. |
| `language` | `string` | `null` | No | Primary language for the bot. If `null`, bot auto-detects user language. |
| `use_emoji` | `bool` | `false` | No | Whether the bot includes emojis in responses. |
| `use_name_reference` | `bool` | `false` | No | Whether the bot addresses the user by name when known. |
| `prompt` | `string` | `null` | No | Custom system prompt override. Appended to dynamically generated instructions. |

**How these affect behavior:**
- `name` → Appears in the greeting: *"Hi! I'm **Aria** from Acme Corp..."*
- `personality` → Injected directly into the main agent's system instructions, shaping tone and style
- `use_emoji` → When `true`, the main agent is instructed to use emojis; when `false`, emojis are suppressed
- `use_name_reference` → When `true` and user's name is known, bot uses it: *"Great question, **Sarah**!"*

---

### Company Fields

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `company_name` | `string` | `""` | Yes | Company name used in responses and context. |
| `company_domain` | `string` | `""` | No | Company website domain. |
| `company_description` | `string` | `""` | Yes | Company overview. Included in system instructions. |
| `industry` | `string` | `""` | Yes | Industry vertical (e.g., "Healthcare", "FinTech"). |
| `category` | `string` | `""` | No | Business category. |
| `sub_category` | `string` | `""` | No | Business sub-category. |
| `business_type` | `string` | `""` | No | Business type (e.g., "B2B", "B2C", "B2B2C"). |
| `business_focus` | `string` | `null` | No | Primary business focus area. |
| `goal_type` | `string` | `null` | No | Primary conversion goal (e.g., "Demo Booking", "Lead Qualification"). |
| `core_usps` | `string` | `""` | No | Core unique selling points. Included in sales instructions. |
| `core_features` | `string` | `""` | No | Core product features summary. |
| `contact_info` | `string` | `""` | No | Company contact information. Shared during escalation. |
| `offer_description` | `string` | `null` | No | Active promotional offer. The bot mentions this when relevant. |

---

### Product Catalog

Products are defined as a list of `Products` objects:

```json
"company_products": [
  {
    "id": "prod_001",
    "name": "Patient Management System",
    "description": "End-to-end patient lifecycle management for hospitals and clinics.",
    "base_pricing": 10000.00,
    "currency": "USD",
    "max_discount_percent": 5.0
  },
  {
    "id": "prod_002",
    "name": "Telemedicine Platform",
    "description": "HD video consultations with integrated e-prescriptions.",
    "base_pricing": 8000.00,
    "currency": "USD",
    "max_discount_percent": 3.0
  }
]
```

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `id` | `string` | — | **Yes** | Unique product identifier. Referenced by negotiation and probing. |
| `name` | `string` | — | **Yes** | Product display name. |
| `description` | `string` | `""` | No | Product description. Used by sales agent for Q&A. |
| `base_pricing` | `float` | `null` | No | Base price. **Protected field** — cannot be lowered by the AI. |
| `currency` | `string` | `"INR"` | No | Currency code for this product. |
| `max_discount_percent` | `float` | `null` | No | Per-product discount cap. Overrides global `negotiation_config.max_discount_percent` when set. |

**How products affect behavior:**
- The sales agent uses product descriptions to answer feature questions
- The negotiation engine reads `base_pricing` and `max_discount_percent` to enforce pricing floors
- The probing agent can detect which product the user is interested in (`detected_product_id`)
- The brochure agent matches asset requests to products

---

### Behavioral Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rules` | `list[string]` | `null` | Hard behavioral constraints injected into system instructions. |

**Rules** are the most powerful behavioral control. Each rule is a string instruction that the bot must follow:

```json
"rules": [
  "Never discuss competitor products by name",
  "Always mention the free trial when discussing pricing",
  "Do not provide medical advice; redirect to qualified professionals",
  "When asked about data security, always mention SOC2 and HIPAA compliance",
  "All pricing is in USD only"
]
```

Rules are injected directly into the main agent's dynamic instructions and are treated as hard constraints by the LLM.

---

### Probing Configuration

Probing is the lead qualification system. When enabled, the bot strategically asks scored questions and triggers a CTA when the score threshold is reached.

#### Top-Level Probing Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_probing` | `bool` | `false` | Master switch for the probing system. |
| `probing_threshold` | `int` | `50` | Total score needed to trigger the CTA. |
| `current_cta` | `string` | `""` | Call-to-action text (e.g., `"Book a Demo"`, `"Talk to Sales"`). |
| `objection_count_limit` | `int` | `3` | Maximum consecutive objections before CTA override. |
| `reset_count_limit` | `int` | `2` | Number of times the objection counter can reset. |

#### Probing Questions

Each question in `probing_questions` is a `ProbingQuestion` object:

```json
"probing_questions": [
  {
    "id": "pq_001",
    "question": "What is the size of your team?",
    "score": 15.0,
    "priority": 1,
    "mandatory": true
  },
  {
    "id": "pq_002",
    "question": "What is your timeline for implementation?",
    "score": 20.0,
    "priority": 2,
    "mandatory": false
  },
  {
    "id": "pq_003",
    "question": "What is your current budget range?",
    "score": 25.0,
    "priority": 3,
    "mandatory": false
  }
]
```

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `id` | `string` | — | **Yes** | Unique question identifier. |
| `question` | `string` | — | **Yes** | The question text. |
| `score` | `float` | `0.0` | No | Points awarded when this question is answered. |
| `priority` | `int` | `null` | No | Order in which questions are asked (lower = earlier). |
| `mandatory` | `bool` | `false` | No | Whether this question must be asked before CTA. |

**Probing flow:**
1. Bot asks the highest-priority unanswered question
2. User answers → score is added to the running total
3. If user declines (objection) → objection counter increments, next question is tried
4. When `total_score >= probing_threshold` → CTA is presented
5. If `objection_count >= objection_count_limit` → CTA is force-presented
6. If user declines CTA → objection counter resets (up to `reset_count_limit` times)
7. After all reset cycles exhausted → probing ends, conversation continues naturally

---

### Negotiation Configuration

```json
"negotiation_config": {
  "max_discount_percent": 5.0,
  "currency": "INR"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_discount_percent` | `float` | `0.0` | Global maximum discount percentage. Acts as a ceiling. |
| `currency` | `string` | `"INR"` | Default currency for pricing discussions. |

**How negotiation works:**
- The negotiation engine uses `base_pricing` from the product and `max_discount_percent` from either the product or this global config
- `base_pricing` is a **protected field** — the AI physically cannot offer a price below `base_pricing × (1 - max_discount_percent/100)`
- Per-product `max_discount_percent` overrides the global setting when present
- Negotiation phases: `initial` → `active` → `closing`
- Once a discount is locked (`discount_locked: true`), no further negotiation occurs for that product

---

### Working Hours

Working hours define when demos can be booked. The default is Mon–Fri 10:00–19:00, with Saturday and Sunday as holidays.

```json
"working_hours": [
  { "day": "Monday",    "type": "Working", "start_time": "10:00", "end_time": "19:00" },
  { "day": "Tuesday",   "type": "Working", "start_time": "10:00", "end_time": "19:00" },
  { "day": "Wednesday", "type": "Working", "start_time": "10:00", "end_time": "19:00" },
  { "day": "Thursday",  "type": "Working", "start_time": "10:00", "end_time": "19:00" },
  { "day": "Friday",    "type": "Working", "start_time": "10:00", "end_time": "19:00" },
  { "day": "Saturday",  "type": "Holiday", "start_time": null,    "end_time": null },
  { "day": "Sunday",    "type": "Holiday", "start_time": null,    "end_time": null }
]
```

| Field | Type | Values | Description |
|-------|------|--------|-------------|
| `day` | `string` | `Monday` through `Sunday` | Day of the week. |
| `type` | `string` | `"Working"` or `"Holiday"` | Whether this day is a work day or holiday. |
| `start_time` | `string` | `HH:MM` format | Start of working hours (24h). `null` for holidays. |
| `end_time` | `string` | `HH:MM` format | End of working hours (24h). `null` for holidays. |

**How working hours affect behavior:**
- Demo booking agent validates requested times against working hours
- Requests outside working hours are rejected with a suggestion for the next available slot
- Requests on holidays are rejected with the next working day offered
- The Calendly integration also checks real-time availability on top of these rules

---

### Assets

Assets are documents the bot can share with prospects (brochures, catalogs, case studies, etc.):

```json
"assets": [
  {
    "asset_id": "brochure_001",
    "asset_name": "Company Brochure 2025",
    "asset_description": "Overview of all products and services",
    "asset_path": "https://cdn.example.com/brochure-2025.pdf",
    "other_info": "Updated quarterly"
  },
  {
    "asset_id": "case_study_001",
    "asset_name": "Healthcare Case Study",
    "asset_description": "How Hospital X improved patient throughput by 40%",
    "asset_path": "https://cdn.example.com/case-study-healthcare.pdf",
    "other_info": null
  }
]
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `asset_id` | `string` | `null` | Unique asset identifier. |
| `asset_name` | `string` | `null` | Display name shown to users. |
| `asset_description` | `string` | `null` | Description used for matching to user requests. |
| `asset_path` | `string` | `null` | URL or file path. Sent as a clickable link. |
| `other_info` | `string` | `null` | Additional metadata. |

**Asset sharing logic:**
- When a user asks for a document, the brochure agent searches `assets` by name/description match
- **One match** → shares directly with the link
- **Multiple matches** → presents options for the user to choose
- **No match** → lists all available assets

---

### Email Templates

Templates used when the conversation switches to email:

```json
"email_template": [
  {
    "id": "tmpl_product_info",
    "name": "Product Information",
    "subject": "Product Details — {{company_name}}",
    "body": "<h2>Product Information</h2><p>Hi {{name}},</p>..."
  },
  {
    "id": "tmpl_followup",
    "name": "Follow-Up",
    "subject": "Following Up — {{company_name}}",
    "body": "<h2>Follow-Up</h2><p>Hi {{name}},</p>..."
  }
]
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `string` | `null` | Template identifier. |
| `name` | `string` | `null` | Template name. Used for context-based matching. |
| `subject` | `string` | `null` | Email subject line. Supports placeholders. |
| `body` | `string` | `null` | Email body (HTML). Supports placeholders. |

---

### Management Contacts

Optional list of company management for escalation or reference:

```json
"company_management": [
  {
    "name": "John Smith",
    "designation": "VP Sales",
    "email": "john@example.com",
    "phone_number": "+1-555-0100"
  }
]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Contact name. |
| `designation` | `string` | Yes | Job title / role. |
| `email` | `string` | Yes | Email address. |
| `phone_number` | `string` | Yes | Phone number. |

---

## How Persona Affects Bot Behavior

The persona is not stored statically — it is **dynamically converted into LLM instructions** at runtime. Here is how each section flows into agent behavior:

```
┌───────────────────────────────────────────────────────────┐
│                    BotPersona (JSON)                       │
└────────────────────────┬──────────────────────────────────┘
                         │
                         ▼
┌───────────────────────────────────────────────────────────┐
│            instructions/generators.py                      │
│   Converts persona fields into natural-language prompts    │
└────────────────────────┬──────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────────┐
    │Main Agent│  │Sales     │  │Booking Agent │
    │          │  │Agent     │  │              │
    │• name    │  │• products│  │• working_hrs │
    │• persona │  │• USPs    │  │• contact_info│
    │• rules   │  │• features│  │              │
    │• emoji   │  │• offer   │  │              │
    └──────────┘  └──────────┘  └──────────────┘
```

**Mapping summary:**

| Persona Field | Agent(s) Affected | Impact |
|---------------|-------------------|--------|
| `name`, `personality` | Main Agent | Greeting style, tone, self-references |
| `company_name`, `company_description` | Main Agent, Sales Agent | Identity and product knowledge |
| `rules` | Main Agent (all conversations) | Hard behavioral constraints |
| `use_emoji` | Main Agent | Emoji presence in responses |
| `use_name_reference` | Main Agent | Whether bot uses user's name |
| `company_products` | Sales Agent, Negotiation Agent | Product Q&A, pricing discussions |
| `core_usps`, `core_features` | Sales Agent | Feature and value prop responses |
| `offer_description` | Sales Agent | Proactive offer mentions |
| `probing_questions`, `probing_threshold` | Probing Agent | Lead qualification flow |
| `current_cta` | Probing Agent, Main Agent | CTA text when qualifying |
| `enable_probing` | Main Agent → Probing Agent | Whether probing is activated |
| `negotiation_config` | Negotiation Agent | Discount limits and currency |
| `working_hours` | Booking Agent | Demo scheduling constraints |
| `assets` | Brochure Agent | Document sharing responses |
| `email_template` | Proceed Email Agent | Email handoff content |

---

## Auto-Setup via Website Crawl

The `/autofill_persona` endpoint automates persona creation by crawling a website.

### How It Works

1. **Crawl** — `Crawl4AI` deep-crawls the website using BFS strategy
2. **Clean** — Markdown is extracted, media URLs are skipped, content is aggressively cleaned and token-limited
3. **Extract** — The `crawl_persona_agent` (powered by Gemini 3 Flash) reads the content and fills in `BotPersona` fields
4. **Ingest** — Crawled content is simultaneously ingested into the Qdrant vector DB as the knowledge base

### API Request

```bash
curl -X POST http://localhost:8000/autofill_persona \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.example.com",
    "user_id": "user_123",
    "tenant_id": "tenant_456",
    "max_depth": 2,
    "max_pages": 50,
    "max_products": 5
  }'
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `url` | `string` | — | — | Website URL to crawl (required). |
| `user_id` | `string` | — | — | User ID for KB ingestion (required). |
| `tenant_id` | `string` | — | — | Tenant ID for vectorDB isolation (required). |
| `max_depth` | `int` | `2` | 1–5 | How many levels deep to crawl. |
| `max_pages` | `int` | `50` | 10–100 | Maximum pages to process. |
| `max_products` | `int` | `5` | 1–100 | Maximum products to extract. |

### Response

```json
{
  "pages_analyzed": 23,
  "urls": ["https://...", "..."],
  "bot_persona": {
    "name": "...",
    "company_name": "...",
    "company_products": [...],
    ...
  }
}
```

### What Gets Auto-Populated

| Field | Auto-Fill Quality | Notes |
|-------|------------------|-------|
| `name` | Good | Derived from company name |
| `company_name` | Excellent | Extracted from site header/footer |
| `company_description` | Excellent | From "About" pages |
| `industry` | Good | Inferred from content |
| `company_products` | Good | Names, descriptions, sometimes pricing |
| `core_usps` | Moderate | Depends on website content |
| `core_features` | Moderate | Depends on website content |
| `contact_info` | Good | From contact pages |
| `probing_questions` | Not populated | Must be configured manually |
| `working_hours` | Populated only if found | Uses defaults (Mon–Fri 10–19) if not found|
| `rules` | Not populated | Must be configured manually |
| `negotiation_config` | Not populated | Must be configured manually |
| `assets` | Not populated | Must be uploaded manually |

**Recommendation:** Use auto-setup as a starting point, then manually configure probing, negotiation, rules, and assets.

---

## Example Configurations

### Example 1: Healthcare SaaS Company

```json
{
  "name": "MedBot",
  "company_name": "HealthFirst Technologies",
  "industry": "Healthcare",
  "category": "Health Tech",
  "sub_category": "Hospital Management",
  "business_type": "B2B",
  "company_description": "HealthFirst provides hospital management software that streamlines patient care, billing, and clinical workflows.",
  "personality": "Professional, empathetic, and knowledgeable about healthcare challenges",
  "use_emoji": false,
  "use_name_reference": true,
  "language": null,
  "goal_type": "Demo Booking",
  "core_usps": "HIPAA compliant, 99.9% uptime, integrates with 50+ EHR systems",
  "core_features": "Patient management, billing automation, telemedicine, analytics dashboard",
  "contact_info": "support@healthfirst.com | +1-800-HEALTH",
  "offer_description": "Free 30-day trial with dedicated onboarding support",
  "rules": [
    "Never provide medical advice",
    "Always mention HIPAA compliance when discussing data security",
    "Do not compare with competitor products directly",
    "Redirect clinical questions to qualified professionals"
  ],
  "company_products": [
    {
      "id": "pms_001",
      "name": "Patient Management System",
      "description": "End-to-end patient lifecycle management including admissions, records, billing, and discharge planning.",
      "base_pricing": 10000.00,
      "currency": "USD",
      "max_discount_percent": 5.0
    },
    {
      "id": "tele_001",
      "name": "Telemedicine Platform",
      "description": "HD video consultations with integrated e-prescriptions and patient messaging.",
      "base_pricing": 8000.00,
      "currency": "USD",
      "max_discount_percent": 3.0
    }
  ],
  "enable_probing": true,
  "probing_threshold": 50,
  "current_cta": "Book a Demo",
  "objection_count_limit": 3,
  "reset_count_limit": 2,
  "probing_questions": [
    { "id": "pq_001", "question": "How many beds does your facility have?", "score": 15.0, "priority": 1, "mandatory": true },
    { "id": "pq_002", "question": "What EHR system are you currently using?", "score": 10.0, "priority": 2, "mandatory": false },
    { "id": "pq_003", "question": "What's your implementation timeline?", "score": 20.0, "priority": 3, "mandatory": false },
    { "id": "pq_004", "question": "What's your annual IT budget for clinical software?", "score": 25.0, "priority": 4, "mandatory": false }
  ],
  "negotiation_config": {
    "max_discount_percent": 5.0,
    "currency": "USD"
  },
  "working_hours": [
    { "day": "Monday",    "type": "Working", "start_time": "09:00", "end_time": "18:00" },
    { "day": "Tuesday",   "type": "Working", "start_time": "09:00", "end_time": "18:00" },
    { "day": "Wednesday", "type": "Working", "start_time": "09:00", "end_time": "18:00" },
    { "day": "Thursday",  "type": "Working", "start_time": "09:00", "end_time": "18:00" },
    { "day": "Friday",    "type": "Working", "start_time": "09:00", "end_time": "17:00" },
    { "day": "Saturday",  "type": "Holiday", "start_time": null,    "end_time": null },
    { "day": "Sunday",    "type": "Holiday", "start_time": null,    "end_time": null }
  ],
  "assets": [
    {
      "asset_id": "brochure_hf",
      "asset_name": "HealthFirst Product Brochure",
      "asset_description": "Complete overview of all HealthFirst products and pricing",
      "asset_path": "https://cdn.healthfirst.com/brochure-2025.pdf",
      "other_info": null
    },
    {
      "asset_id": "case_study_hf",
      "asset_name": "City Hospital Case Study",
      "asset_description": "How City Hospital reduced wait times by 35% using our platform",
      "asset_path": "https://cdn.healthfirst.com/case-study-city-hospital.pdf",
      "other_info": null
    }
  ],
  "email_template": [
    {
      "id": "tmpl_product",
      "name": "Product Information",
      "subject": "HealthFirst Product Details",
      "body": "<h2>Thank you for your interest!</h2><p>Here are the details we discussed...</p>"
    }
  ]
}
```

### Example 2: Minimal Persona (Quick Start)

The bare minimum to get a working bot:

```json
{
  "name": "SalesBot",
  "company_name": "My Company",
  "industry": "Technology",
  "company_description": "We build software solutions for businesses.",
  "company_products": [
    {
      "id": "prod_001",
      "name": "Main Product",
      "description": "Our flagship software solution."
    }
  ]
}
```

All other fields use defaults. Probing is disabled, negotiation has 0% discount, working hours are Mon–Fri 10–19.

### Example 3: Lead Qualification Focus (No Booking)

```json
{
  "name": "QualifyBot",
  "company_name": "Enterprise Solutions Inc",
  "industry": "Enterprise Software",
  "company_description": "Enterprise-grade workflow automation.",
  "personality": "Consultative and data-driven",
  "enable_probing": true,
  "probing_threshold": 40,
  "current_cta": "Schedule a Consultation",
  "probing_questions": [
    { "id": "pq_001", "question": "What industry is your company in?", "score": 10.0, "priority": 1, "mandatory": true },
    { "id": "pq_002", "question": "How many employees does your organization have?", "score": 15.0, "priority": 2, "mandatory": false },
    { "id": "pq_003", "question": "What's your biggest operational challenge right now?", "score": 20.0, "priority": 3, "mandatory": false }
  ],
  "company_products": [
    { "id": "prod_001", "name": "WorkflowPro", "description": "Automated workflow management." }
  ],
  "rules": [
    "Focus on understanding business pain points",
    "Do not discuss pricing until qualification is complete"
  ]
}
```

---

## Best Practices

### Persona Identity

1. **Choose a human-sounding name** — `"Aria"` or `"Alex"` feels more natural than `"SalesBot_v2"`.
2. **Write personality as you'd describe a person** — `"Warm, professional, always curious about customer challenges"` works better than `"formal tone"`.
3. **Set `use_name_reference: true`** for B2B conversations where personalization matters.
4. **Set `use_emoji: false`** for enterprise/healthcare verticals; `true` for consumer/casual contexts.

### Products

5. **Always include `id` fields** — Negotiation and probing reference products by ID.
6. **Write rich descriptions** — The sales agent uses descriptions to answer feature questions. More detail = better answers.
7. **Set `base_pricing` on every product** if you want negotiation to work — without a price, there's nothing to negotiate.
8. **Set per-product `max_discount_percent`** for fine-grained control (e.g., 5% on Product A, 0% on Product B).

### Probing Questions

9. **Start with 3–5 questions** for a natural conversation flow. More than 8 feels like an interrogation.
10. **Score by qualification value** — Budget and timeline questions should score higher than demographic ones.
11. **Set threshold to ~60–70% of total possible score** — Ensures CTA triggers after most key questions without requiring all of them.
12. **Make 1–2 questions mandatory** — Usually company size and use case.
13. **Order by priority** — Ask easier/less intrusive questions first (company industry → team size → budget).

### Negotiation

14. **Start with `max_discount_percent: 0`** if you don't want any negotiation. The bot will state the price as fixed.
15. **Keep discounts modest** (3–5%) — The bot negotiates better with small increments.
16. **Set the `currency` field** to avoid confusion in multi-currency scenarios.

### Rules

17. **Be specific** — `"Never mention competitor X by name"` is better than `"Don't talk about competitors"`.
18. **Use positive framing when possible** — `"Always redirect medical questions to qualified professionals"` is clearer than `"Don't give medical advice"`.
19. **Limit to 5–10 rules** — Too many rules can conflict and confuse the LLM.
20. **Test rules explicitly** — Send a message that should trigger the rule and verify the bot respects it.

### Working Hours

21. **Match your actual availability** — If you can't do Friday demos, mark Friday as Holiday.
22. **Use 24-hour format** — `"09:00"` to `"18:00"`, not `"9 AM"` to `"6 PM"`.
23. **Consider your prospects' timezone** — Booking uses the prospect's timezone for comparison with your working hours.

### Assets

24. **Use descriptive names and descriptions** — The matching algorithm uses these fields. `"Company Brochure 2025"` is better than `"brochure_v3_final"`.
25. **Use publicly accessible URLs** — The bot shares `asset_path` directly; ensure the link works without authentication.
26. **Include diverse asset types** — Brochures, case studies, datasheets, and pricing sheets cover different prospect needs.

---

## Troubleshooting

### Bot doesn't mention products

- **Check:** Are `company_products` populated with descriptions?
- **Check:** Is the knowledge base (RAG) ingested with product information?
- **Fix:** Add product descriptions and/or run `/autofill_persona` to populate the KB.

### Probing questions aren't asked

- **Check:** Is `enable_probing` set to `true`?
- **Check:** Is `probing_questions` a non-empty list?
- **Check:** Is `current_cta` set? The system needs a CTA to trigger.
- **Fix:** Set all three fields. Example: `"enable_probing": true, "current_cta": "Book a Demo"`.

### Bot ignores negotiation / gives no discounts

- **Check:** Does the product have `base_pricing` set?
- **Check:** Is `max_discount_percent` > 0 (either per-product or in `negotiation_config`)?
- **Fix:** Set `base_pricing` on the product and a non-zero discount cap.

### Bot books on weekends / outside hours

- **Check:** Is `working_hours` properly configured with Saturday/Sunday as `"Holiday"`?
- **Check:** Are `start_time` and `end_time` in `HH:MM` 24-hour format?
- **Fix:** Verify all 7 days are present in the working hours array.

### Auto-setup returns empty products

- **Check:** Does the website have a clear products/services page?
- **Try:** Increase `max_depth` to 3 or `max_pages` to 100.
- **Try:** Increase `max_products` parameter.
- **Note:** Complex single-page apps (SPAs) may not crawl well. Manual setup may be needed.

### Rules aren't being followed

- **Check:** Are rules written as clear, unambiguous instructions?
- **Try:** Rephrase the rule more specifically.
- **Note:** Rules compete with other instructions. Keep them concise and non-contradictory.

### Bot responds in wrong language

- **Check:** Is `language` set? If set, the bot defaults to that language.
- **Fix:** Set `language: null` to let the bot auto-detect the user's language.
