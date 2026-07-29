# BotRunner Product Features — Customer Onboarding Guide

> **Last Updated:** March 6, 2026 &nbsp;|&nbsp; **Version:** 2.1.0  
> **Audience:** New Customers, Business Users, Sales Teams

---

## Welcome to BotRunner

BotRunner is your **24/7 AI sales assistant** — a conversational AI platform that talks to your prospects, answers their questions about your products, qualifies them as leads, handles pricing discussions, and books demos — all automatically.

Think of it as adding a tireless, always-on salesperson to your team who knows everything about your company and products.

---

## Table of Contents

- [What BotRunner Does](#what-botrunner-does)
- [Feature 1: Intelligent Product Q&A](#feature-1-intelligent-product-qa)
- [Feature 2: Automated Demo Booking](#feature-2-automated-demo-booking)
- [Feature 3: Smart Lead Qualification](#feature-3-smart-lead-qualification)
- [Feature 4: Pricing & Negotiation](#feature-4-pricing--negotiation)
- [Feature 5: Follow-up Reminders](#feature-5-follow-up-reminders)
- [Feature 6: Human Agent Handoff](#feature-6-human-agent-handoff)
- [Feature 7: Email Handoff](#feature-7-email-handoff)
- [Feature 8: Document & Brochure Sharing](#feature-8-document--brochure-sharing)
- [Feature 9: Custom Persona Configuration](#feature-9-custom-persona-configuration)
- [Feature 10: Website-Based Auto-Setup](#feature-10-website-based-auto-setup)
- [Feature 11: WhatsApp Template Generation](#feature-11-whatsapp-template-generation)
- [Feature 12: Multi-Language Support](#feature-12-multi-language-support)
- [Feature 13: Security & Quality Guardrails](#feature-13-security--quality-guardrails)
- [Industry Use Cases](#industry-use-cases)
- [Getting Started — Onboarding Checklist](#getting-started--onboarding-checklist)
- [FAQ](#faq)

---

## What BotRunner Does

| What Your Prospect Does | What BotRunner Does |
|------------------------|---------------------|
| Asks about your products | Answers instantly using your knowledge base |
| Shows interest | Qualifies them with smart follow-up questions |
| Asks about pricing | Handles negotiation within your approved limits |
| Wants a demo | Books it directly on your calendar |
| Needs to think about it | Sets a follow-up reminder |
| Wants to talk to a person | Prepares a summary and hands off to your team |
| Asks for a brochure | Shares the right document instantly |

---

## Feature 1: Intelligent Product Q&A

**What it does:** BotRunner answers product and company questions by searching your knowledge base in real time.

**How it works:**
- You upload your product documents, FAQ pages, or website content
- BotRunner indexes everything into a searchable knowledge base
- When a prospect asks a question, BotRunner finds the most relevant answer and responds naturally

**Benefits:**
- Prospects get instant, accurate answers — even at 2 AM
- No more lost leads because of slow response times
- Answers are always up-to-date with your latest product info

**Configuration:**
- Upload product PDFs, datasheets, and FAQ documents
- OR use the auto-setup feature to crawl your website automatically
- Define your product catalog with names, descriptions, and key features

**Example:**
> **Prospect:** "What does your telemedicine platform include?"  
> **BotRunner:** "Our Telemedicine Platform includes HD video consultations, secure patient messaging, e-prescriptions, and integration with major EHR systems. It's designed for clinics expanding their reach. Want to see a demo?"

---

## Feature 2: Automated Demo Booking

**What it does:** BotRunner collects the prospect's details and books a demo directly on your calendar, integrated with Calendly.

**How it works:**
1. Prospect says they want a demo
2. BotRunner collects their email, preferred date/time, and product interest
3. BotRunner checks your calendar availability in real time
4. If the slot is available, it's booked. If not, alternatives are offered.
5. Prospect receives a calendar invite

**Supports:**
- **New bookings** — Schedule a fresh demo
- **Rescheduling** — Change an existing appointment
- **Cancellation** — Cancel a booked demo

**Smart date understanding:**
- Natural phrases: "next Tuesday at 3 PM", "tomorrow morning", "in 2 days"
- Working hours enforcement: only books during your business hours
- Weekend detection: suggests the next available weekday

**Configuration:**
- Set your working hours (e.g., Mon–Fri, 10 AM – 7 PM)
- Connect your Calendly account

---

## Feature 3: Smart Lead Qualification

**What it does:** BotRunner asks strategic, scored questions to qualify prospects — then triggers a call-to-action when they're ready.

**How it works:**
1. You define probing questions (e.g., "What's your team size?", "What's your timeline?")
2. Each question has a score (e.g., 15 points, 20 points)
3. As the prospect answers, their score increases
4. When the score reaches your threshold, BotRunner presents a call-to-action (e.g., "Book a Demo")

**Smart objection handling:**
- If a prospect declines to answer, BotRunner doesn't push — it moves to the next question
- After a set number of objections, it gently offers the CTA anyway
- If they continue objecting, BotRunner backs off entirely and continues the conversation naturally

**Configuration:**
- Define your probing questions with scores and priorities
- Set the score threshold for CTA trigger (default: 50)
- Choose your CTA: "Book a Demo", "Schedule a Meeting", "Talk to Sales", or custom
- Set objection limits and reset cycles
- Enable/disable the entire probing system per persona

---

## Feature 4: Pricing & Negotiation

**What it does:** BotRunner handles pricing conversations and can offer discounts within limits you define — without giving away the farm.

**How it works:**
- Prospect asks about pricing → BotRunner presents the list price
- If the prospect pushes back → BotRunner can discuss value and offer small concessions
- Discounts are capped at your maximum (e.g., 5% off) — the AI cannot go beyond this limit
- Base prices are protected — the AI cannot accidentally lower your prices

**Configuration:**
- Set base prices per product
- Set maximum discount percentage per product (e.g., 5%)
- Optionally set negotiation currency

**Example:**
> **Prospect:** "How much is the Patient Management System?"  
> **BotRunner:** "The Patient Management System is priced at $10,000/year, including all core features and 24/7 support."  
> **Prospect:** "That's a bit over our budget."  
> **BotRunner:** "I understand. I can offer a special 3% discount, bringing it to $9,700/year. That's a great deal for everything included."

---

## Feature 5: Follow-up Reminders

**What it does:** When a prospect isn't ready to commit, BotRunner schedules a follow-up at their preferred time.

**How it works:**
- Prospect says "remind me later" or "contact me tomorrow"
- BotRunner asks for their timezone (or detects it automatically)
- Schedules a follow-up at the specified time 
- Your team is notified when it's time to follow up

**Smart time understanding:**
- "in 30 minutes", "tomorrow afternoon", "next week"
- Supports Hindi time expressions ("do ghante baad" = in 2 hours)
- Timezone-aware: resolves from country/region automatically

**Configuration:**
- No additional configuration needed — works out of the box

---

## Feature 6: Human Agent Handoff

**What it does:** When a prospect wants to speak to a real person, BotRunner prepares a comprehensive handoff package for your team.

**What your team receives:**
- **Conversation summary** — What was discussed
- **Key topics** — Main areas of interest
- **User sentiment** — How the prospect is feeling
- **Contact details** — Email (validated), name, company
- **Open questions** — What the prospect still wants to know

**Benefits:**
- Your sales rep walks in fully briefed — no "can you repeat that?"
- Faster handoff = better prospect experience
- Sentiment insight helps your rep adjust their approach

---

## Feature 7: Email Handoff

**What it does:** When a prospect prefers email communication, BotRunner switches the conversation to email with a pre-formatted summary.

**How it works:**
1. Prospect says "email me the details"
2. BotRunner collects their email (if not already known)
3. Matches the conversation to the right email template
4. Generates an HTML email with conversation highlights

**Configuration:**
- Define email templates for different scenarios (product info, pricing, follow-up)
- Templates are matched automatically based on conversation context

---

## Feature 8: Document & Brochure Sharing

**What it does:** BotRunner shares relevant documents, brochures, and datasheets when prospects ask.

**How it works:**
- Prospect asks for a document → BotRunner matches to your asset library
- One match → shares it directly with download link
- Multiple matches → shows options for the prospect to choose
- No match → lists everything available

**Configuration:**
- Upload your assets: brochures, catalogues, case studies, datasheets, whitepapers
- Each asset has a name, description, and download link/path

---

## Feature 9: Custom Persona Configuration

**What it does:** Define exactly who your bot is — its name, personality, what it knows, and how it behaves.

**What you can configure:**
- **Bot identity:** Name, company, industry
- **Personality:** Communication style (e.g., "Professional and warm", "Casual and friendly")
- **Products:** Full catalog with descriptions and pricing
- **Rules:** Custom behavioral rules (e.g., "Never discuss competitor pricing")
- **Assets:** Documents available for sharing
- **Working hours:** When demos can be booked
- **Email templates:** For email handoff scenarios
- **Probing setup:** Lead qualification questions and thresholds
- **Negotiation limits:** Maximum discounts and pricing rules

See the [Persona Guide](PERSONA_GUIDE.md) for complete configuration details.

---

## Feature 10: Website-Based Auto-Setup

**What it does:** Point BotRunner at your website and it automatically generates a complete bot persona — name, products, company info, and knowledge base.

**How it works:**
1. Provide your website URL
2. BotRunner crawls your site (up to 50 pages)
3. Extracts company info, products, features, and pricing
4. Generates a ready-to-use bot persona
5. Ingests the content into the knowledge base

**Benefits:**
- Go from zero to a working bot in minutes
- No manual data entry needed
- Knowledge base populated automatically

**Configuration:**
- Website URL (required)
- Crawl depth (1–5 levels, default: 2)
- Maximum pages (10–100, default: 50)
- Maximum products to extract (1–100, default: 5)

---

## Feature 11: WhatsApp Template Generation

**What it does:** Automatically generates WhatsApp Business API message templates for each of your products.

**What you get:**
- Marketing templates with product highlights
- Proper variable placeholders (e.g., `{{Customer Name}}`)
- Buttons (URLs, quick replies)
- Formatted for WhatsApp Business API submission

**Configuration:**
- Products from your persona (automatic)
- Maximum templates per product

---

## Feature 12: Multi-Language Support

**What it does:** BotRunner detects the prospect's language and responds in kind — no configuration needed.

**How it works:**
- Prospect writes in Spanish → BotRunner responds in Spanish
- Prospect writes in Hindi → BotRunner responds in Hindi
- Prospect switches mid-conversation → BotRunner adapts

**Supported:**
- All major languages supported by the underlying LLM
- Hindi number words supported for time expressions (e.g., "do ghante" = 2 hours)
- Script detection (Roman, Devanagari, etc.)

---

## Feature 13: Security & Quality Guardrails

**What it does:** Two layers of protection ensure your bot stays safe and on-brand.

**Input protection:**
- Detects prompt injection, jailbreak attempts, and data extraction attacks
- Records incidents for security monitoring
- Designed to never block legitimate users — records but doesn't block

**Output quality:**
- 12 validation rules check every bot response before it reaches the prospect
- Prevents: off-topic responses, fabricated information, fake contact details, tone violations, data privacy leaks
- If a response fails quality check, it's automatically replaced with a safe alternative

---

## Industry Use Cases

### Healthcare Technology
- Product: Patient Management System, Telemedicine
- Bot handles: Feature Q&A, compliance questions, demo booking with clinical staff
- Key value: 24/7 availability for busy healthcare professionals

### SaaS / B2B Software
- Product: Enterprise software subscriptions
- Bot handles: Feature comparison, pricing tiers, trial scheduling
- Key value: Automated lead qualification before human follow-up

### Financial Services
- Product: Trading platforms, wealth management tools
- Bot handles: Product features, regulatory FAQ, advisor booking
- Key value: Guardrails prevent unauthorized financial advice

### Education Technology
- Product: LMS, assessment platforms
- Bot handles: Feature demos, pricing for institutions, pilot booking
- Key value: Multi-language support for global education markets

### Real Estate
- Product: Property management software, CRM
- Bot handles: Feature walkthrough, pricing, consultation booking
- Key value: Follow-up reminders for long sales cycles

---

## Getting Started — Onboarding Checklist

Use this checklist to get your BotRunner instance up and running:

### Step 1: Basic Setup
- [ ] Provide your company name and industry
- [ ] Choose a bot name and personality tone
- [ ] Define your target audience

### Step 2: Products & Pricing
- [ ] List your products/services with descriptions
- [ ] Set base prices for each product
- [ ] Set maximum discount percentages (for negotiation)

### Step 3: Knowledge Base
- [ ] Option A: Provide your website URL for auto-crawl setup
- [ ] Option B: Upload product documents (PDFs, datasheets)
- [ ] Verify knowledge base accuracy with test questions

### Step 4: Lead Qualification (Optional)
- [ ] Enable probing system
- [ ] Define 3–8 probing questions with scores
- [ ] Set the score threshold for CTA trigger
- [ ] Choose your CTA text (e.g., "Book a Demo")

### Step 5: Demo Booking
- [ ] Set working hours (business days and times)
- [ ] Mark weekends
- [ ] Connect Calendly account
- [ ] Test a booking flow end-to-end

### Step 6: Assets & Templates
- [ ] Upload brochures, catalogs, and case studies
- [ ] Define email templates for different scenarios
- [ ] Optionally generate WhatsApp templates

### Step 7: Rules & Guardrails
- [ ] Define any custom rules (e.g., "Never mention competitor X")
- [ ] Test the bot with adversarial inputs to verify guardrails

### Step 8: Go Live
- [ ] Run comprehensive test conversations
- [ ] Verify multi-language responses (if applicable)
- [ ] Monitor first 50 conversations via admin panel
- [ ] Adjust persona, probing questions, and rules based on feedback

---

## FAQ

**Q: How long does setup take?**  
A: With the website auto-setup feature, you can have a working bot in 15–30 minutes. Manual configuration takes 1–2 hours for a comprehensive setup.

**Q: Can I change the bot's personality after launch?**  
A: Yes! The persona can be updated at any time. Changes take effect immediately for new conversations.

**Q: What happens if the AI doesn't know the answer?**  
A: The bot will acknowledge it doesn't have specific information and offer to connect the prospect with your team — it never makes up answers.

**Q: Can the bot give unauthorized discounts?**  
A: No. Pricing guardrails are enforced at the system level. The AI physically cannot exceed the maximum discount you configure, regardless of what a prospect asks.

**Q: Is my data secure?**  
A: Yes. Each company gets isolated sessions and a separate knowledge base. Input/output guardrails prevent data leakage. No conversation data is shared across tenants.

**Q: What if my website changes?**  
A: You can re-run the auto-setup crawl at any time to refresh the persona and knowledge base with updated content.

**Q: Can I see the conversation logs?**  
A: Yes, the admin panel (Streamlit UI) lets you view all conversations, inspect bot state, and monitor performance.

**Q: Does it work in languages other than English?**  
A: Yes. The bot automatically detects the prospect's language and responds accordingly. No separate language configuration is needed.
