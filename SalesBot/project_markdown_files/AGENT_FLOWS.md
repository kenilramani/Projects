# BotRunner Agent Conversation Flows — QA Reference

> **Last Updated:** March 6, 2026 &nbsp;|&nbsp; **Version:** 2.1.0  
> **Audience:** QA Engineers, Support Engineers, Product Managers  
> **Purpose:** End-to-end conversation flow guide covering every intent, handoff, CTA, and edge case

---

## Table of Contents

- [System Overview](#system-overview)
- [Agent Inventory](#agent-inventory)
- [1. Main (Triage) Agent](#1-main-triage-agent)
  - [1.1 Greeting Flow](#11-greeting-flow)
  - [1.2 Product Inquiry → Sales Handoff](#12-product-inquiry--sales-handoff)
  - [1.3 Demo/Meeting Request → Booking Handoff](#13-demomeeting-request--booking-handoff)
  - [1.4 Follow-up Request → Followup Handoff](#14-follow-up-request--followup-handoff)
  - [1.5 Human Escalation Request](#15-human-escalation-request)
  - [1.6 Email Communication Request](#16-email-communication-request)
  - [1.7 Asset/Brochure Request](#17-assetbrochure-request)
  - [1.8 Pricing/Negotiation Request](#18-pricingnegotiation-request)
  - [1.9 Ambiguous or Off-Topic Input](#19-ambiguous-or-off-topic-input)
- [2. Sales Agent](#2-sales-agent)
- [3. Demo Booking Agent](#3-demo-booking-agent)
  - [3.1 New Booking Flow](#31-new-booking-flow)
  - [3.2 Reschedule Flow](#32-reschedule-flow)
  - [3.3 Cancel Flow](#33-cancel-flow)
  - [3.4 Confirmation Acknowledgment](#34-confirmation-acknowledgment)
- [4. Follow-up Agent](#4-follow-up-agent)
- [5. Human Escalation Agent](#5-human-escalation-agent)
- [6. Probing System](#6-probing-system)
  - [6.1 Probing Happy Path](#61-probing-happy-path)
  - [6.2 Objection Handling During Probing](#62-objection-handling-during-probing)
  - [6.3 Objection Limit and Reset Cycle](#63-objection-limit-and-reset-cycle)
  - [6.4 CTA Trigger Conditions](#64-cta-trigger-conditions)
- [7. Negotiation Engine](#7-negotiation-engine)
- [8. Asset Sharing (Brochure) Flow](#8-asset-sharing-brochure-flow)
- [9. Proceed-with-Email Flow](#9-proceed-with-email-flow)
- [10. Lead Analysis](#10-lead-analysis)
- [11. Guardrails](#11-guardrails)
  - [11.1 Input Guardrail](#111-input-guardrail)
  - [11.2 Output Guardrail](#112-output-guardrail)
- [12. Cross-Agent Workflows](#12-cross-agent-workflows)
- [13. Supported Intents Summary](#13-supported-intents-summary)
- [14. All CTAs in the System](#14-all-ctas-in-the-system)
- [15. Error and Edge Case Behavior](#15-error-and-edge-case-behavior)

---

## System Overview

BotRunner uses a **multi-agent orchestration** pattern built on the OpenAI Agents SDK. Every user message enters through the **Main (Triage) Agent** (`main_agent`), which:

1. Passes through the **input guardrail** (security check — record-only, fail-open)
2. Classifies user intent
3. Either responds directly **OR** hands off to a specialized agent
4. The specialized agent handles the request and returns a structured `BotResponse`
5. The response passes through the **output guardrail** (quality check — can block)
6. State is finalized, persisted, and returned to the API caller

```
User Message
    │
    ▼
┌────────────────────┐
│  Input Guardrail   │──── Matches SAFE_CONVERSATIONAL_PATTERNS? → Fast-path (no LLM)
│                    │──── Otherwise → LLM classification (record-only, never blocks)
└────────┬───────────┘
         ▼
┌────────────────────┐        ┌────────────────────────┐
│   Main Agent       │──hand──│ sales_agent             │  (product/feature queries)
│   (Triage)         │──off──►│ demo_booking_agent      │  (book/reschedule/cancel)
│                    │──────►│ followup_agent           │  (reminders, follow-ups)
│                    │──────►│ human_agent              │  (escalation to live agent)
│   Tools:           │        └────────────────────────┘
│   • proceed_email  │─── agent-as-tool (email switch)
│   • negotiation    │─── agent-as-tool (pricing/discounts)
│   • asset_sharing  │─── agent-as-tool (brochures/docs)
└────────┬───────────┘
         ▼
┌────────────────────┐
│  Output Guardrail  │──── approved="no"? → Use suggested_text fallback
│                    │──── guardrail error? → Fail-open (pass original)
└────────┬───────────┘
         ▼
    API Response (BotResponse → APIResponse)
```

---

## Agent Inventory

| Agent | Internal Name | Type | Purpose |
|-------|--------------|------|---------|
| Main / Triage | `main_agent` | Root | Intent classification, routing, direct responses |
| Sales | `sales_agent` | Handoff child | Product info, features, use RAG for KB lookup |
| Demo Booking | `demo_booking_agent` | Handoff child | Book/reschedule/cancel demos |
| Follow-up | `followup_agent` | Handoff child | Schedule follow-up reminders |
| Human Escalation | `human_agent` | Handoff child | Transfer to live human support |
| Lead Analysis | `lead_analysis_agent` | Agent-as-tool | Classify leads (hot/warm/cold) — used inside booking |
| Proceed Email | `switch_to_email_agent` | Agent-as-tool | Switch communication to email channel |
| Negotiation Engine | `negotiation_engine_agent` | Agent-as-tool | Handle pricing and discount negotiation |
| Asset Sharing | `asset_sharing_agent` | Agent-as-tool | Share brochures, PDFs, documents |
| Objection Handle | `objection_handle_agent` | Agent-as-tool | Handle user objections — used inside sales |
| Probing | `probing_agent` | Standalone (API) | Generate probing questions for a persona |
| Probing Instructions | `probing_instruction_agent` | Standalone (API) | Generate probing instruction text |
| Template Generation | `template_generation_agent` | Standalone (API) | Generate WhatsApp message templates |
| Crawl Persona | — | Standalone (API) | Crawl website → auto-fill BotPersona + ingest KB |

### Handoff vs Tool Distinction

- **Handoff agents** (sales, booking, followup, human): Main agent transfers full control. The child agent runs with its own instructions and tools. State is mutated via a `on_*_handoff` callback.
- **Tool agents** (negotiation, email, asset sharing, objection): Called inline by the main or sales agent. The calling agent retains control and incorporates the tool's output into its response.

---

## 1. Main (Triage) Agent

**Internal name:** `main_agent`  
**Dynamic instructions:** `main_prompt(state)` from `app/prompts/instruction.py`  
**Handoffs:** `sales_agent`, `demo_booking_agent`, `followup_agent`, `human_agent`  
**Tools:** `proceed_with_email`, `negotiation_engine`, `proceed_with_asset_sharing`  
**Input guardrails:** `[input_attack]`  
**Output schema:** `BotResponse`

### 1.1 Greeting Flow

**Trigger:** User sends a greeting or conversational filler.  
**Examples:** "Hi", "Hello", "Hey there", "Good morning", "hmm", "ok"

**Processing:**
1. Input guardrail: matches `SAFE_CONVERSATIONAL_PATTERNS` → fast-path bypass (no LLM call)
2. Main agent generates personalized greeting using bot persona (name, company)
3. Response returned directly — no handoff

**Example Conversation:**
```
User: "Hi there!"
Bot:  "Hello! I'm Arya from AI Sante. How can I help you today?"

User: "Good morning"
Bot:  "Good morning! Welcome to AI Sante. I'd be happy to tell you
       about our solutions or help you schedule a demo. What interests you?"
```

**Verify:**
- Response includes bot persona name (`bot_persona.name`) and company (`bot_persona.company_name`)
- No handoff occurs — `last_agent` stays `main_agent`
- Input guardrail records `classification: "safe"` without an LLM call
- Output guardrail still runs on the response

---

### 1.2 Product Inquiry → Sales Handoff

**Trigger:** User asks about products, features, pricing details, or company info.  
**Sample keywords:** "What products do you offer?", "Tell me about your features", "company info", "how does X compare?"

**Processing:**
1. Input guardrail: LLM-based check → classified as `safe`
2. Main agent detects product/sales intent
3. Handoff to `sales_agent` via `on_sales_handoff` callback
4. Callback sets: `new_booking=True`, `user_language`, `user_script`
5. Sales agent uses `retrieve_query` tool (RAG) to fetch knowledge from Qdrant
6. Returns product information response

**Example Conversation:**
```
User: "What solutions do you offer for healthcare?"

Processing:
  → main_agent detects product inquiry → handoff to sales_agent
  → on_sales_handoff: new_booking=True
  → sales_agent calls retrieve_query("healthcare solutions")
  → RAG returns relevant docs from tenant's knowledge base

Bot:  "Great question! AI Sante offers several healthcare solutions:
       1. Patient Management System — Streamlines patient records…
       2. Telemedicine Platform — Enables virtual consultations…
       Would you like to learn more about any of these?"
```

**Verify:**
- `last_agent` = `sales_agent`
- `new_booking` = `True`
- `retrieve_query` tool called with meaningful search terms
- Response draws on knowledge base content (if KB is populated for the tenant)

---

### 1.3 Demo/Meeting Request → Booking Handoff

**Trigger:** User wants to book, schedule, reschedule, or cancel a demo/meeting.  
**Sample keywords:** "Book a demo", "Schedule a call", "I'd like a meeting", "Can I see a demo?", "Reschedule", "Cancel my appointment"

**Processing:**
1. Main agent detects booking intent
2. Handoff to `demo_booking_agent` via `on_demo_handoff` callback
3. Callback sets: `new_booking=True`, updates language/script
4. Booking agent begins collecting mandatory fields

**Example Conversation:**
```
User: "I'd like to book a demo"

Processing:
  → main_agent → handoff to demo_booking_agent
  → on_demo_handoff: new_booking=True

Bot:  "I'd be happy to help you book a demo! Let me collect a few
       details. Could you please share your email address?"
```

**Verify:**
- `last_agent` = `demo_booking_agent`
- `new_booking` = `True`
- Bot begins asking for mandatory booking fields (email, date/time, products)

---

### 1.4 Follow-up Request → Followup Handoff

**Trigger:** User wants a reminder or later contact.  
**Sample keywords:** "Remind me later", "Ping me in 5 minutes", "Contact me tomorrow", "Follow up next week"

**Processing:**
1. Main agent detects follow-up intent
2. Handoff to `followup_agent` via `on_followup_handoff` callback
3. Callback sets: `follow_trigger=True`
4. Followup agent collects timezone and datetime

**Example Conversation:**
```
User: "Can you remind me in 30 minutes?"

Processing:
  → main_agent → handoff to followup_agent
  → on_followup_handoff: follow_trigger=True

Bot:  "Sure! I'll set a reminder for you. Could you let me know
       your region or timezone so I can schedule it accurately?"

User: "I'm in India"

Processing:
  → get_timezone("IN") → timezone="Asia/Kolkata"
  → process_followup_datetime("in 30 minutes", "Asia/Kolkata")

Bot:  "Got it! I'll follow up with you in 30 minutes (at 3:30 PM IST).
       Is there anything specific you'd like me to cover?"
```

**Verify:**
- `last_agent` = `followup_agent`
- `follow_trigger` = `True`
- `followup_details.followup_flag` = `True`
- `followup_details.followup_time` is a valid UTC ISO 8601 timestamp
- `timezone` correctly resolved from region code

---

### 1.5 Human Escalation Request

**Trigger:** User explicitly asks to speak to a human.  
**Sample keywords:** "Talk to a human", "I want to speak with someone", "Connect me with your team", "Let me talk to a real person", "Get me a manager"

**Processing:**
1. Main agent detects human escalation intent
2. Handoff to `human_agent` via `on_human_handoff` callback
3. Callback sets: `human_requested=True`, `escalation_timestamp=<UTC ISO>`, `last_agent="human_agent"`
4. Human agent collects context: conversation summary, sentiment, email

**Example Conversation:**
```
User: "I want to speak with a real person"

Processing:
  → main_agent → handoff to human_agent
  → on_human_handoff: human_requested=True, escalation_timestamp=<now>

Bot:  "I completely understand. Let me connect you with a team member.
       To ensure a smooth handoff, could you share your email address?"

User: "john@gmial.com"

Processing:
  → validate_email("john@gmial.com")
  → typo_detected=True, suggestion="john@gmail.com"

Bot:  "I noticed your email might have a typo — did you mean john@gmail.com?"

User: "Yes, that's right"

Bot:  "Great, I've noted john@gmail.com. I'm preparing a summary of our
       conversation for the team. They'll be in touch shortly."
```

**Verify:**
- `last_agent` = `human_agent`
- `human_requested` = `True`
- `escalation_timestamp` is set (UTC ISO string)
- Email typo detection works for common domains
- `human_details.summary` populated
- `human_details.key_topics` populated
- `human_details.user_sentiment` classified
- `human_details.ready_for_handoff` = `True` when handoff prep is complete

---

### 1.6 Email Communication Request

**Trigger:** User wants to continue via email.  
**Sample keywords:** "Send me an email", "Continue over email", "Email me the details", "Can you email that?"

**Processing:**
1. Main agent detects email intent
2. Calls `proceed_with_email` tool (agent-as-tool, not a handoff)
3. Tool checks if user email is already available in state
4. If no email → asks user for email address (`get_email_flag=False`)
5. If email available → matches conversation to available email templates, generates HTML body
6. Returns `ProceedEmailDetails` with template info

**Example Conversation:**
```
User: "Can you email me the details we discussed?"

Processing:
  → main_agent calls proceed_with_email tool
  → Checks state for user email → not found

Bot:  "I'd be happy to email you! Could you please share your email address?"

User: "john@company.com"

Processing:
  → Tool receives email → matches template from persona.email_template
  → Generates HTML reply_body

Bot:  "I've prepared an email summary of our conversation. It will be
       sent to john@company.com shortly with all the details."
```

**Verify:**
- `proceed_email_details.switch_to_email` = `True`
- `proceed_email_details.get_email_flag` = `True` (after email collected)
- `proceed_email_details.reply_body` contains HTML content
- `proceed_email_details.email_template_id` and `email_template_name` set if template matched

---

### 1.7 Asset/Brochure Request

**Trigger:** User asks for documents, brochures, datasheets, catalogues, files.  
**Sample keywords:** "Send me a brochure", "Do you have a datasheet?", "Can I get the PDF?", "Share your catalogue"

**Processing:**
1. Main agent calls `proceed_with_asset_sharing` tool
2. Tool matches request against `persona.assets[]`
3. Single match → returns asset details directly
4. Multiple matches → presents numbered options for user to choose
5. No match → lists all available assets

**Example Conversation:**
```
User: "Do you have a product brochure?"

Processing:
  → main_agent calls proceed_with_asset_sharing tool
  → Matches against persona.assets → single match found

Bot:  "Absolutely! Here's our product brochure:
       📄 AI Sante Product Catalog
       Download: [link to asset]
       Would you like to know more about any specific product?"
```

**Verify:**
- `brochure_flag` = `True`
- `brochure_details.asset_id`, `asset_name`, `asset_path` populated
- If multiple assets match, bot presents numbered options
- If no assets configured on persona, bot informs user

---

### 1.8 Pricing/Negotiation Request

**Trigger:** User discusses pricing, asks for discounts, mentions budget constraints.  
**Sample keywords:** "How much does it cost?", "Any discounts?", "Too expensive", "My budget is X", "Can you be flexible on pricing?"

**Processing:**
1. Main agent calls `negotiation_engine` tool (never answers pricing directly)
2. Negotiation engine uses discount strategy based on product config
3. Protected fields: `active_base_price` and `max_discount_percent` are system-managed
4. Stage-aware responses: initial inquiry → pushback → deeper concession → final offer

**Example Conversation:**
```
User: "How much does the Patient Management System cost?"

Processing:
  → main_agent calls negotiation_engine tool
  → Engine detects product → returns pricing response

Bot:  "The Patient Management System is priced at ₹50,000/year.
       This includes all core features plus 24/7 support.
       Would you like to discuss how this fits your requirements?"

User: "That's a bit over our budget. Can you do better?"

Processing:
  → negotiation_engine called again → phase: active, attempts: 2
  → Offers discount within max_discount_percent

Bot:  "I understand budget considerations are important. I can offer
       a special 3% discount, bringing it to ₹48,500/year."
```

**Verify:**
- Main agent NEVER responds to pricing directly — always calls negotiation_engine
- `negotiation_state.negotiation_session` populated with product details
- `current_discount_percent` never exceeds `max_discount_percent` (default 5%)
- `active_base_price` never changes from system-set value (protected field)
- `discount_locked` = `True` after final offer accepted

---

### 1.9 Ambiguous or Off-Topic Input

**Trigger:** User sends unclear, off-topic, or unrelated messages.

**Behavior:**
- Conversational fillers ("hmm", "ok", "I see") → acknowledged naturally, conversation continues
- Off-topic questions ("What's the weather?") → politely redirected to relevant topics
- Ambiguous intent → helpful response offering available actions

**Example Conversation:**
```
User: "hmm"
Bot:  "Take your time! I'm here whenever you have questions about
       our solutions or would like to schedule a demo."

User: "What's the weather like today?"
Bot:  "I appreciate the question! I'm focused on helping you with
       our products and services. Would you like to learn about
       our solutions or schedule a demo?"

User: "maybe"
Bot:  "No rush at all! Here's what I can help with:
       • Learn about our products and features
       • Book a demo or meeting
       • Get pricing information
       • Connect with our team
       What sounds interesting to you?"
```

---

## 2. Sales Agent

**Internal name:** `sales_agent`  
**Tools:** `retrieve_query` (RAG), `objection_handle_tool` (agent-as-tool for objection handling)  
**Dynamic instructions:** `sales_prompt(state)` from `app/prompts/dynamic_sales.py`

### Happy Path: Product Information

```
[Handoff from main_agent via on_sales_handoff]

User: "Tell me about your telemedicine features"

Processing:
  → sales_agent calls retrieve_query("telemedicine features")
  → RAG retrieves docs from Qdrant (tenant-isolated collection)
  → Agent composes response using KB context + persona

Bot:  "Our Telemedicine Platform includes:
       • HD video consultations
       • Secure patient messaging
       • E-prescriptions
       • Integration with major EHR systems

       It's designed for clinics that want to expand their reach.
       Would you like to see it in action with a demo?"
```

### KB Miss (Empty or Irrelevant Knowledge Base)

```
User: "What's your API rate limit?"

Processing:
  → retrieve_query("API rate limit") → no relevant docs found
  → Agent falls back to persona-defined product info

Bot:  "I don't have specific API details on hand, but I can connect
       you with our technical team who can share full integration
       documentation. Would you like me to arrange that?"
```

### Objection During Sales Conversation

```
User: "I don't think we need that kind of solution"

Processing:
  → sales_agent detects objection
  → Calls objection_handle_tool (objection_handle_agent.as_tool())
  → Objection handler classifies: type="soft"
  → Uses RAG for a knowledge-backed re-engagement response

Bot:  "I understand your concern. Many of our current clients felt
       the same way initially. What specific challenges are you
       facing with your current setup? Understanding your needs
       can help me show the most relevant features."
```

**Verify:**
- `retrieve_query` is called with relevant search terms
- Response draws on knowledge base content when available
- Objections are handled empathetically, not aggressively
- Bot stays in character per `persona.personality`
- `objection_state.objection_analysis.type_of_objection` set to `"soft"`, `"hard"`, or `"hidden"`

---

## 3. Demo Booking Agent

**Internal name:** `demo_booking_agent`  
**Tools:** `process_booking_datetime`, `check_calendly_availability`, `get_timezone`, `lead_analysis_tool`  
**Dynamic instructions:** `booking_prompt(state)` from `app/prompts/demo_booking.py`

### Mandatory Fields for Booking

| Field | Source | Required |
|-------|--------|----------|
| `email` | `contact_details` or collected during conversation | Yes |
| `products` | Auto-selected from negotiation, or asked explicitly | Yes |
| `date` | Collected via `process_booking_datetime` | Yes |
| `time` | Collected via `process_booking_datetime` | Yes |
| `timezone` | Resolved via `get_timezone` | Yes (for UTC conversion) |

### 3.1 New Booking Flow

**Trigger:** User requests a new demo/meeting.  
**Booking type:** `"new"`

**Full Multi-Turn Example:**
```
[Handoff from main_agent → demo_booking_agent]

Bot:  "I'd love to help you book a demo! Let me collect a few details.
       What's your email address?"

User: "sarah@company.com"
  → Stores email in collected_fields

Bot:  "Thank you, Sarah! Which product are you interested in seeing?
       We have:
       1. Patient Management System
       2. Telemedicine Platform"

User: "The patient management one"
  → Stores product selection

Bot:  "When would you prefer the demo? Please share a date and time."

User: "How about tomorrow at 2 PM?"

Processing:
  → get_timezone (if not set) → resolved from region
  → process_booking_datetime("tomorrow at 2 PM", "Asia/Kolkata")
    → Parses: date=2026-03-08, time=14:00
    → Validates: not past ✓, not weekend? (Saturday!) ✗
    → Returns: success=False, is_weekend=True

Bot:  "Tomorrow is a Saturday and we don't have demo slots on weekends.
       How about Monday at 2 PM instead?"

User: "Monday works"

Processing:
  → process_booking_datetime("Monday at 2 PM", "Asia/Kolkata")
    → Parses: date=2026-03-09, time=14:00
    → Validates: all checks pass ✓
    → convert_to_utc → 2026-03-09T08:30:00Z
  → check_calendly_availability("2026-03-09T08:30:00Z", tenant_id, "Asia/Kolkata")
    → is_available=True

Bot:  "Your demo is confirmed for Monday, March 9th at 2:00 PM IST.
       You'll receive a calendar invite at sarah@company.com.
       Is there anything specific you'd like us to cover?"

Processing (post-confirmation):
  → booking_confirmed=True
  → lead_analysis_tool called → classifies lead as hot/warm/cold
```

**Verify:**
- `booking_fields.booking_type` = `"new"`
- `booking_fields.booking_confirmed` = `True` ONLY when `check_calendly_availability` returns `is_available=True`
- `collected_fields.email` = `"sarah@company.com"`
- `collected_fields.date` = `"2026-03-09"` (YYYY-MM-DD format)
- `collected_fields.time` = UTC ISO 8601 string
- `lead_details` populated after booking confirmation
- Weekend dates rejected with alternative suggestion
- Past dates rejected
- Times outside working hours rejected

### Working Hours Validation

| Rule | Default Value | Configurable Via |
|------|--------------|-----------------|
| Working days | Monday–Friday | `persona.working_hours` |
| Working time | 10:00–19:00 | `persona.working_hours[].start_time/end_time` |
| Holiday days | Saturday–Sunday | `persona.working_hours[].type = "Holiday"` |
| Max future | 6 months | Hardcoded in `_validate_booking_datetime` |
| Minimum | Not in the past | Hardcoded in `_validate_booking_datetime` |

### 3.2 Reschedule Flow

**Trigger:** User wants to change an existing booking.  
**Prerequisite:** `booking_confirmed` = `True`  
**Booking type:** `"reschedule"`

```
User: "I need to reschedule my demo"

Bot:  "Of course! When would you prefer the new time?"

User: "Next Wednesday at 11 AM"

Processing:
  → process_booking_datetime("next Wednesday at 11 AM", timezone)
  → Validates → passes all checks
  → check_calendly_availability → is_available=True

Bot:  "Your demo has been rescheduled to Wednesday, March 12th at
       11:00 AM IST. The original slot has been released."
```

**Critical reschedule rules:**
- If the new slot is **unavailable**, the ORIGINAL booking remains valid
- Agent suggests alternative times from `alternative_slots[]`
- `lead_analysis_tool` called again after successful reschedule
- `booking_type` is immutable once set — stays `"reschedule"` throughout

### 3.3 Cancel Flow

**Trigger:** User wants to cancel an existing booking.  
**Prerequisite:** `booking_confirmed` = `True`  
**Booking type:** `"cancel"`

```
User: "I want to cancel my demo"

Bot:  "I'm sorry to hear that. Are you sure you'd like to cancel
       your demo scheduled for Wednesday, March 12th at 11:00 AM?"

User: "Yes, cancel it"

Bot:  "Your demo has been cancelled. If you change your mind,
       I'm here to help you rebook anytime."
```

**Verify:**
- `booking_fields.booking_confirmed` = `False` after cancellation
- `lead_analysis_tool` is NOT called for cancellations

### 3.4 Confirmation Acknowledgment

**Trigger:** User acknowledges a confirmed booking without new information.  
**Intent type:** `ACKNOWLEDGMENT`

```
User: "Sounds good, thanks"
Bot:  "You're welcome! Your demo is all set. Looking forward to it!"
```

**Verify:** No tools called. No state changes. Just a natural acknowledgment.

### Datetime Parsing Capabilities

The `process_booking_datetime` tool handles these expression types:

| Expression Type | Examples |
|----------------|----------|
| Relative | "in 2 hours", "in 3 days", "next week" |
| Day names | "Monday", "next Tuesday", "this Friday" |
| Time of day | "morning" → 10:00, "afternoon" → 14:00, "evening" → 18:00 |
| Explicit dates | "March 15th", "15/03/2026", "2026-03-15", "9th Dec" |
| Combined | "tomorrow at 3 PM", "next Monday morning", "March 15 at 2:30 PM" |
| AM/PM | "3 PM", "3pm", "15:00" |
| Ordinals | "9th December", "the 15th" |
| Word-to-number | "three o'clock" |

**Default:** When time is not specified, defaults to 10:00 AM (`time_defaulted=True`).

---

## 4. Follow-up Agent

**Internal name:** `followup_agent`  
**Tools:** `get_timezone`, `process_followup_datetime`  
**Dynamic instructions:** `followup_prompt(state)` from `app/prompts/followup.py`

### Happy Path

```
[Handoff from main_agent → followup_agent]

User: "Remind me in 30 minutes"

Processing:
  → Check timezone: if not set, ask for region
  → process_followup_datetime("in 30 minutes", "Asia/Kolkata")
  → Parses: now + 30 min
  → Validates: not past ✓, not >90 days ✓
  → Converts to UTC

Bot:  "I'll follow up with you in 30 minutes at 3:30 PM IST.
       Is there anything specific you'd like me to cover?"
```

### Hindi Number Word Support

The follow-up datetime parser supports **Hindi** number words:

| Hindi Word | Number |
|------------|--------|
| ek | 1 |
| do | 2 |
| teen | 3 |
| char | 4 |
| panch | 5 |
| das | 10 |
| pandrah | 15 |
| bees | 20 |
| tees | 30 |
| pachas | 50 |

**Example:**
```
User: "do ghante baad remind karo"  (remind in 2 hours)
→ process_followup_datetime("do ghante baad", timezone) → now + 2 hours
```

### Special Follow-up Expressions

| Expression | Parsing |
|-----------|---------|
| "half hour" | 30 minutes |
| "couple of hours" | 2 hours |
| "quarter hour" | 15 minutes |
| "morning" | 10:00 AM |
| "afternoon" | 2:00 PM |
| "evening" | 6:00 PM |
| "night" | 8:00 PM |

### Follow-up Validation Rules

| Rule | Limit |
|------|-------|
| Past time | Rejected |
| Maximum future | 90 days |

**Verify:**
- `followup_details.followup_flag` = `True`
- `followup_details.followup_time` = UTC ISO 8601 timestamp
- `followup_details.timezone_confirmed` = `True`
- `timezone` correctly resolved for the user

---

## 5. Human Escalation Agent

**Internal name:** `human_agent`  
**Tools:** None (email validation handled within prompt logic)  
**Output guardrails:** `[output_guardrail]` — responses are quality-checked  
**Dynamic instructions:** `human_agent_prompt(state)` from `app/prompts/human_agent.py`

### Full Flow

```
[Handoff from main_agent → human_agent]

Bot:  "I understand you'd like to speak with a team member. Let me
       prepare a handoff. Could you share your email so our team
       can reach out to you?"

User: "john@company.com"

Processing:
  → validate_email → is_valid=True
  → Agent summarizes conversation

Bot:  "Thank you, John. I've prepared a summary of our conversation:

       📋 Handoff Summary:
       • Topics: Product features, pricing
       • Sentiment: Interested but has concerns
       • Open questions: Integration capabilities, pricing flexibility

       Our team will reach out at john@company.com."

User: "Please mention we need SSO support"

Bot:  "Noted! I've added SSO support requirements to the handoff.
       Our team will be in touch shortly."
```

**Verify:**
- `human_requested` = `True`
- `escalation_timestamp` set to UTC ISO string
- `human_details.summary` populated
- `human_details.key_topics` has list of discussion topics
- `human_details.user_sentiment` classified
- `human_details.email_validated` = `True` when email provided
- `human_details.ready_for_handoff` = `True` when preparation is complete

### Email Typo Detection Table

| Mistyped Domain | Auto-Suggested Correction |
|----------------|--------------------------|
| gmial.com | gmail.com |
| gmal.com | gmail.com |
| yaho.com | yahoo.com |
| outlok.com | outlook.com |
| hotmal.com | hotmail.com |
| iclud.com | icloud.com |
| protonmal.com | protonmail.com |

---

## 6. Probing System

The probing system qualifies leads through scored questions woven into natural conversation. It operates within the main agent when `enable_probing=True` in the persona.

### Key Configuration (Per Persona)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enable_probing` | `False` | Master switch for probing |
| `probing_threshold` | `50` | Score needed to trigger CTA |
| `objection_count_limit` | `3` | Max objections before CTA trigger |
| `reset_count_limit` | `2` | Max reset cycles before freeze |
| `probing_questions` | `[]` | List of `ProbingQuestion` objects |
| `current_cta` | `""` | CTA text (e.g., "Book a Demo") |

### ProbingQuestion Structure

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier |
| `question` | string | The exact question text |
| `score` | float | Points awarded when the question is answered |
| `priority` | int | Lower number = asked first |
| `mandatory` | bool | Must be asked before optional questions at the same priority |

### 6.1 Probing Happy Path

```
[Persona has probing enabled with these questions:]
Q1: "What is your team size?" (score=15, priority=1, mandatory=True)
Q2: "What tools do you currently use?" (score=20, priority=2, mandatory=True)
Q3: "What's your timeline for implementation?" (score=20, priority=3)
Q4: "What's your budget range?" (score=25, priority=4)
Threshold: 50 | CTA: "Book a Demo"

---
User: "Hi, I'm interested in your product"
Bot:  "Welcome! I'd love to learn more about your needs.
       How large is your team?"
[State: total_score=0]

User: "We have about 50 people"
  → Match Q1 → is_answered=True
  → score_to_add=15, total_score=15 (< 50) → continue
  → Next: Q2 (priority=2, mandatory)
Bot:  "A 50-person team is a great fit! What tools are you
       currently using for patient management?"
[State: total_score=15, answered=1]

User: "We use spreadsheets and a basic CRM"
  → Match Q2 → is_answered=True
  → score_to_add=20, total_score=35 (< 50) → continue
  → Next: Q3 (priority=3)
Bot:  "Spreadsheets can be limiting as you grow. When are you
       looking to make a change — is there a timeline?"
[State: total_score=35, answered=2]

User: "We need something in place by Q2"
  → Match Q3 → is_answered=True
  → score_to_add=20, total_score=55 (>= 50!)
  → probing_completed=True, can_show_cta=True
Bot:  "That's a solid timeline! Based on what you've shared, I think
       a demo would be the perfect next step. Would you like to
       **Book a Demo** to see how we can help your team?"
[State: total_score=55, probing_completed=True, can_show_cta=True]
```

**Verify:**
- `probing_context.total_score` increments correctly per question
- `probing_context.probing_completed` = `True` when threshold met
- `probing_context.can_show_cta` = `True` when threshold met
- Questions asked in priority order (lowest number first)
- Mandatory questions asked before optional at same priority level
- `probing_context.detected_question_answer` array has all Q/A pairs

### 6.2 Objection Handling During Probing

```
Bot:  "What tools are you currently using?"

User: "I'd rather not share that"

Processing:
  → Classified as objection → is_objection=True
  → score_to_add=0, is_answered=False
  → objection_handle_agent called via tool
  → Classifies: type="soft"
  → objection_count: 0 → 1

Bot:  "No problem at all! I understand privacy concerns. I was just
       trying to understand your setup to give better recommendations.
       Let me ask something else — what's your timeline for
       implementation?"
```

**Objection Types:**

| Type | Description | Example |
|------|-------------|---------|
| `soft` | Low engagement, recoverable disinterest | "I'm not interested" |
| `hard` | Direct, strong refusal | "I don't want to answer that" |
| `hidden` | Underlying concern masked by deflection | "I'll think about it" |

**Verify:**
- `objection_state.current_objection_count` increments by 1
- `score_to_add` = 0 for objections
- `objection_state.objection_analysis.type_of_objection` classified
- Bot moves to next question rather than repeating the current one

### 6.3 Objection Limit and Reset Cycle

**Flow when user hits the objection limit:**

```
[objection_count = 2, limit = 3]

User: "I don't want to answer these questions"
  → is_objection=True → objection_count: 2 → 3
  → 3 >= 3 (limit) → is_objection_limit_reached=True
  → can_show_cta=True

Bot:  "I completely respect that. Based on what we've discussed so
       far, **Book a Demo** where our team can address all your
       questions directly. Would you like to schedule one?"

[NEXT MESSAGE — Reset cycle begins:]

User: "Not right now, tell me more about your product"
  → Previous: is_objection_limit_reached was True
  → limit_reach_count: 0 → 1
  → Reset objection_count to 0
  → Continue conversation normally (probing resumes)

[IF limit_reach_count reaches reset_count_limit (default 2):]
  → FREEZE: objection count stops incrementing
  → CTA disabled — no more probing pressure
  → Conversation continues naturally without probing
```

**State Machine:**
```
Normal Probing
    ├── Answer → score += value → threshold met? → Show CTA → Booking handoff
    ├── Objection → count++ → limit reached? → Show CTA
    │                                               │
    │                                          Next message → Reset cycle
    │                                               ├── reset count < limit? → Resume
    │                                               └── reset count >= limit? → FREEZE
    └── Product query → answer via RAG → re-ask current probing question
```

### 6.4 CTA Trigger Conditions

| Condition | CTA Shown? | Outcome |
|-----------|-----------|---------|
| `total_score >= probing_threshold` | **Yes** | Handoff to booking if user accepts |
| `objection_count >= objection_count_limit` | **Yes** | Handoff to booking if user accepts |
| `probing_completed=True` from prior turn | **Yes** | CTA persists |
| Score below threshold, no objection limit | **No** | Continue probing |
| FROZEN (`limit_reach_count >= reset_count_limit`) | **No** | CTA disabled; normal conversation |

---

## 7. Negotiation Engine

**Internal name:** `negotiation_engine_agent`  
**Used as:** `negotiation_engine` tool on the root agent  
**Output type:** `NegotiationAgentResponse`  
**Dynamic instructions:** `get_pricing_negotiation_prompt(state)` from `app/prompts/negotiation.py`

### Configuration

| Parameter | Default | Source |
|-----------|---------|--------|
| `max_discount_percent` | 5.0 | `persona.negotiation_config` or per-product `Products.max_discount_percent` |
| `currency` | "INR" | `persona.negotiation_config.currency` |

### Protected Fields (System-Managed, Not Overwritable by LLM)
- `active_base_price` — from product catalog
- `max_discount_percent` — from product catalog or negotiation config

### Negotiation Phases

| Phase | Description | Typical Discount |
|-------|-------------|-----------------|
| `initial` | First price inquiry | 0% (full price shown) |
| `active` | User pushback, negotiation rounds | Small incremental discount |
| `closing` | Final offer | Up to `max_discount_percent` |

### Multi-Turn Negotiation Example

```
Turn 1:
  User: "How much is the Patient Management System?"
  → negotiation_engine: initial phase → shows full price (₹50,000)

Turn 2:
  User: "That seems expensive"
  → negotiation_engine: active phase → value reinforcement or small discount

Turn 3:
  User: "My budget is ₹47,000"
  → Engine records user_budget_constraint=47000
  → Offers closer to budget if within max_discount (e.g., 3% → ₹48,500)

Turn 4:
  User: "Can you do ₹45,000?"
  → Below max discount floor → "The best I can offer is ₹47,500"
  → discount_locked=True
```

**Verify:**
- `negotiation_state.negotiation_session.negotiated_products[]` populated
- `negotiation_attempts` increments monotonically (never decreases)
- `current_discount_percent` never exceeds `max_discount_percent`
- `discount_locked` = `True` after final offer
- Main agent NEVER reveals maximum discount ceiling
- `active_base_price` never changes — protected by `NegotiationEngine`

---

## 8. Asset Sharing (Brochure) Flow

**Internal name:** `asset_sharing_agent`  
**Used as:** `proceed_with_asset_sharing` tool on root agent  
**Dynamic instructions:** `asset_sharing_prompt(state)` from `app/prompts/asset_sharing.py`

### Matching Logic

| Scenario | Bot Behavior |
|----------|-------------|
| Single asset matches request | Returns asset details (id, name, path) directly |
| Multiple assets match | Lists options and asks user to choose |
| No assets match | Lists all available assets |
| No assets configured | Informs user no documents are available |

### Asset Model

Each asset is defined in `persona.assets[]` with:
- `asset_id` — unique identifier
- `asset_name` — display name
- `asset_description` — what the asset contains
- `asset_path` — URL or file path for download
- `other_info` — additional metadata

**Verify:**
- `brochure_flag` = `True` when an asset is shared
- `brochure_details.asset_path` contains the download URL/path
- `brochure_details.asset_name` and `asset_id` populated

---

## 9. Proceed-with-Email Flow

**Internal name:** `switch_to_email_agent`  
**Used as:** `proceed_with_email` tool on root agent  
**Dynamic instructions:** `proceed_with_email_prompt(state)` from `app/prompts/proceed_with_email.py`

### Decision Tree

```
Email request detected
    │
    ├── User email already in state?
    │       │
    │       ├── Yes → Match template → Generate HTML body → 
    │       │         switch_to_email=True, get_email_flag=True
    │       │
    │       └── No → Ask for email → get_email_flag=False
    │
    └── (User provides email in follow-up)
            │
            └── Match template → Generate reply_body →
                switch_to_email=True, get_email_flag=True
```

**Verify:**
- `proceed_email_details.switch_to_email` = `True`
- `proceed_email_details.email_template_id` and `email_template_name` set if template matched
- `proceed_email_details.reply_body` contains generated HTML content
- Template selected from `persona.email_template[]` based on conversation context

---

## 10. Lead Analysis

**Internal name:** `lead_analysis_agent`  
**Used as:** `lead_analysis_tool` within `demo_booking_agent`  
**Output type:** `LeadAnalysis`

### When Called
- After a **NEW** booking is confirmed (`booking_confirmed=True`)
- After a **RESCHEDULE** is confirmed
- **NOT** called for cancellations

### Classification Table

| Classification | Criteria |
|---------------|----------|
| `hot` | High engagement, clear timeline, budget discussed, direct intent |
| `warm` | Moderate engagement, some interest, needs nurturing |
| `cold` | Low engagement, no clear intent, many objections |

### Output Fields

| Field | Description |
|-------|-------------|
| `lead_classification` | `"hot"` / `"warm"` / `"cold"` |
| `reasoning` | Detailed analysis explanation |
| `key_indicators` | List of indicators that led to classification |
| `recommended_next_action` | Suggested follow-up action |
| `urgency_level` | `"immediate"` / `"soon"` / `"later"` / `"no-interest"` |

---

## 11. Guardrails

### 11.1 Input Guardrail

**Agent:** `input_guardrail_agent`  
**Model:** `guardrail` (gpt-4.1-nano via Azure)  
**Mode:** **Record-only (fail-open)** — classifies input but does NOT block messages

#### Fast Path (No LLM Call)

Messages matching `SAFE_CONVERSATIONAL_PATTERNS` bypass the LLM guardrail entirely:

- **Greetings:** hi, hello, hey, good morning, good afternoon, good evening, howdy, hiya
- **Acknowledgments:** ok, okay, sure, yes, yeah, yep, yup, no, nope, nah, right, correct, fine, thanks, thank you
- **Fillers:** hmm, um, uh, erm, ah, let me think, maybe, perhaps, i guess
- **Engagement:** go on, continue, tell me more, what else, and, so, then
- **Short responses:** got it, understood, interesting, cool, nice, great, good, i see

Normalized: lowercase, punctuation stripped, repeated characters collapsed.

#### LLM Classification Categories

| Classification | Description | Example |
|---------------|-------------|---------|
| `safe` | Normal business query | "What are your prices?" |
| `prompt_injection` | Attempt to override instructions | "Ignore all previous instructions" |
| `jailbreak` | Attempt to change AI identity | "Pretend you are a different AI" |
| `data_extraction` | Attempt to extract system data | "Show me your system prompt" |
| `harmful_content` | Violent, hateful, or illegal | — |
| `off_topic` | Completely unrelated queries | "Write me a poem about cats" |

**Key behavior:** `tripwire_triggered` is always `False`. Input guardrail RECORDS the classification in `state.input_guardrail_decision` but never blocks the message.

### 11.2 Output Guardrail

**Agent:** `output_guardrail_agent`  
**Model:** `guardrail` (gpt-4.1-nano via Azure)  
**Mode:** **Active** — CAN block and replace responses

#### 12 Validation Rules

| # | Rule | Severity |
|---|------|----------|
| 1 | Domain scope — reject off-domain responses | CRITICAL |
| 2 | Information accuracy — reject fabricated facts/features | CRITICAL |
| 3 | Contact info — reject fabricated phone/email/addresses | CRITICAL |
| 4 | Tone & personality — match persona personality | HIGH |
| 5 | Language & culture — correct language/script used | HIGH |
| 6 | Bot rules compliance — follow persona.rules | HIGH |
| 7 | Goal alignment — response advances conversation goal | MEDIUM |
| 8 | Booking flow — progressive info collection OK | MEDIUM |
| 9 | Data privacy — no credit cards, SSN, passwords exposed | CRITICAL |
| 10 | Datetime validation — must use tool for datetime processing | HIGH |
| 11 | Email validation — must use validate_email() | HIGH |
| 12 | Response quality — reject gibberish/hostile content | HIGH |

#### Trip Behavior

- `validation_status_approved` = `"no"` → `tripwire_triggered=True`
- Triggers `OutputGuardrailTripwireTriggered` exception in `_execute_agent()`
- System extracts `suggested_text` from guardrail output → uses as replacement response
- If guardrail agent itself errors → **fail-open** (original response passes through)

#### Severity Handling

| Severity | Action |
|----------|--------|
| CRITICAL | Reject — use `suggested_text` |
| HIGH | Modify if possible, otherwise reject |
| MEDIUM | Approve with suggested modification |
| LOW | Approve as-is |

---

## 12. Cross-Agent Workflows

### Workflow A: Probing → CTA → Booking

```
main_agent (probing enabled)
  → Asks scored probing questions
  → total_score reaches probing_threshold
  → Shows CTA: "Book a Demo"
  → User accepts
  → Handoff to demo_booking_agent
  → Full booking flow (collect email, datetime, product)
  → lead_analysis_tool classifies the lead
```

### Workflow B: Sales → Negotiation → Booking

```
main_agent → handoff to sales_agent
  → User asks about pricing details
  → main_agent calls negotiation_engine tool
  → Multiple negotiation rounds (initial → active → closing)
  → User satisfied with price: "Let's book a demo"
  → Handoff to demo_booking_agent
  → Products auto-selected from negotiation (no need to re-ask)
```

### Workflow C: Booking → Unavailable → Follow-up

```
demo_booking_agent
  → Slot unavailable, user can't find a good time
  → User: "Can you just ping me tomorrow?"
  → Handoff to followup_agent
  → Schedule follow-up reminder
```

### Workflow D: Any Point → Human Escalation

```
[At any point during any conversation]
  → User: "Let me talk to someone on your team"
  → Immediate handoff to human_agent (regardless of current agent)
  → Conversation context preserved in human_details
```

### Workflow E: Sales → Objection → Asset Share → Booking

```
main_agent → handoff sales_agent
  → User asks about product
  → User objects: "I need to see proof"
  → Objection handled with empathetic response
  → main_agent calls proceed_with_asset_sharing
  → Brochure/datasheet shared with user
  → User: "OK let's book a demo"
  → Handoff to demo_booking_agent
```

---

## 13. Supported Intents Summary

| Intent | Sample Triggers | Agent | Action Type |
|--------|----------------|-------|-------------|
| Greeting | hi, hello, hey, good morning | main_agent | Direct response |
| Product inquiry | products, features, what do you offer, compare | sales_agent | Handoff |
| Pricing inquiry | how much, cost, price, pricing | main_agent → negotiation_engine | Tool call |
| Discount request | discount, cheaper, best price, budget is X | main_agent → negotiation_engine | Tool call |
| Book demo | book a demo, schedule a call, set up a meeting | demo_booking_agent | Handoff |
| Reschedule | reschedule, change the time, move my meeting | demo_booking_agent | Handoff |
| Cancel booking | cancel, don't need the demo anymore | demo_booking_agent | Handoff |
| Follow-up | remind me, ping later, come back tomorrow | followup_agent | Handoff |
| Human escalation | talk to human, real person, manager, your team | human_agent | Handoff |
| Email request | email me, send by email, continue over email | main_agent → proceed_email | Tool call |
| Asset/document | brochure, PDF, datasheet, catalogue, whitepaper | main_agent → asset_sharing | Tool call |
| Objection | not interested, don't need, I'll pass | sales_agent → objection_handle | Tool call |
| Acknowledgment | ok, sure, hmm, yes, thanks, got it | main_agent | Direct response |
| Off-topic | weather, jokes, unrelated topics | main_agent | Polite redirect |
| Attack/injection | ignore instructions, system prompt, jailbreak | input_guardrail | Recorded (not blocked) |

---

## 14. All CTAs in the System

| CTA Text | When Triggered | Configuration |
|----------|---------------|---------------|
| **Book a Demo** | Probing score threshold reached | `persona.current_cta = "Book a Demo"` |
| **Schedule a Meeting** | Probing threshold or objection limit | `persona.current_cta = "Schedule a Meeting"` |
| **Talk to Sales** | Probing threshold or objection limit | `persona.current_cta = "Talk to Sales"` |
| **Conversational** | Never triggered explicitly | `persona.current_cta = "Conversational"` — no explicit CTA push |
| Custom CTA | Persona-configured | Any string in `persona.current_cta` |

**CTA trigger conditions (all depend on `enable_probing=True`):**

1. `total_score >= probing_threshold` → Show CTA
2. `objection_count >= objection_count_limit` → Show CTA
3. All probing questions answered → Show CTA
4. `probing_completed=True` from previous turn → Persist CTA

**CTA acceptance flow:**
- User accepts → Handoff to `demo_booking_agent` (for booking-type CTAs) or appropriate agent
- User declines → Conversation continues; CTA may be shown again if conditions re-met

---

## 15. Error and Edge Case Behavior

### LLM Provider Failure
- Primary (Azure GPT-5.1) fails → auto-fallback to OpenAI GPT-5.1 → Gemini 3 Flash
- Fallback is transparent to user — no error message shown
- Each model role has independent fallback: primary, guardrail, summarizer

### Null or Empty Agent Response
- If agent returns null/empty response → system generates contextual fallback
- Fallback uses last agent name and conversation context for continuity

### Output Guardrail Trip
- Response fails quality check → `suggested_text` from guardrail replaces original
- If guardrail agent itself errors → fail-open (original response used)

### Session Not Found
- New session created with default state + empty persona
- Conversation starts fresh

### Calendly Slot Unavailable
- Requested slot not available → alternative slots from `alternative_slots[]` suggested
- If no alternatives → `ask_new_date=True`, user asked to propose a different time
- For reschedule: original booking remains valid if new slot isn't available

### Invalid Datetime Expressions

| Error | Bot Response |
|-------|-------------|
| Past date/time | "That time has already passed. Could you suggest a future date?" |
| Weekend | "We only have slots on weekdays. How about [next weekday]?" |
| Outside working hours | "Our available hours are 10 AM to 7 PM. Could you pick a time in that range?" |
| More than 6 months out | "Please pick a date within the next 6 months." |
| Unparseable | "I couldn't understand that date. Could you try in a format like 'March 15 at 2 PM'?" |

### Semantic Cache Behavior
- Similar query (cosine similarity > 0.5) → cached response returned (no LLM call)
- Cache is per-user session, maximum 15 entries (FIFO)
- Embeddings via Azure OpenAI

### Multi-Language Handling
- Bot detects `user_language` and `user_script` from the conversation
- Responds in the same language the user uses
- Probing questions translated to user's detected language
- All tool inputs (datetime expressions) are translated to English internally before tool processing
- Follow-up datetime parser supports Hindi number words natively
