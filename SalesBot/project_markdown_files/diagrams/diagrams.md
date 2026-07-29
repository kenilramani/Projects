# BotRunner — All Diagrams

> **Source:** Extracted from all documentation files in `docs/`
> **Format:** Mermaid

---

## From ARCHITECTURE.md

### System Architecture Diagram

```mermaid
flowchart TD
    subgraph CLIENT["CLIENT LAYER"]
        CL1["Streamlit UI /chat_ui"]
        CL2["API Clients /chat"]
        CL3["Webhooks"]
    end

    subgraph FASTAPI["FASTAPI SERVER - main.py"]
        FA["/health /chat /chat_ui\n/autofill_persona /generate_*\n/cache_stats /generate_templates"]
    end

    subgraph PIPELINE["EXECUTION PIPELINE - app_agent.py"]
        P1["Session Load"] --> P2["Semantic Cache"] --> P3["Agent Run"] --> P4["State Finalize"] --> P5["Persist & Return"]
        P1 -.-> PE1["Probing Engine State"]
        P3 -.-> PE2["Negotiation Engine\n(protected $)"]
    end

    subgraph AGENTS["AGENT ORCHESTRATION LAYER"]
        ROOT["ROOT AGENT - main_agent\nInput Guardrail → Intent Classification → Route"]
        ROOT -->|"Handoff"| SA["Sales Agent"]
        ROOT -->|"Handoff"| DBA["Demo Booking Agent"]
        ROOT -->|"Handoff"| FUA["Followup Agent"]
        ROOT -->|"Handoff"| HA["Human Agent"]
        SA -.-> OH["Objection Handler"]
        DBA -.-> LA["Lead Analysis"]
        FUA -.-> TZ["Timezone Resolver"]
        ROOT -.->|"Tool"| NE["Negotiate Engine"]
        ROOT -.->|"Tool"| ES["Email Switch"]
        ROOT -.->|"Tool"| AS["Asset Sharing"]
    end

    subgraph INFRA["INFRASTRUCTURE"]
        LLM["LLM ROUTER - LiteLLM\nAzure GPT-5.1 → OpenAI → Gemini"]
        DATA["DATA LAYER\nSQLite / Neon PG\nSemantic Cache"]
        RAG["RAG PIPELINE\nQdrant / ChromaDB\nFastEmbed + Reranker"]
    end

    CLIENT --> FASTAPI --> PIPELINE --> AGENTS
    AGENTS --> LLM
    AGENTS --> DATA
    AGENTS --> RAG
```

### Execution Pipeline (10-Step)

```mermaid
flowchart TD
    S1["1. Session Load\nget_or_create_session → BotState\nMerge request with existing state"]
    S2["2. State Initialization\nProbingEngineState.from_state\nNegotiationEngine.from_state\nGenerate message_id UUID v4"]
    S3{"3. Semantic Cache Check\nretrieve_from_cache"}
    S3HIT["Cache Hit - similarity > 0.5\nReturn cached response"]
    S4["4. Agent Execution\nRunner.run with RunContextWrapper\nHandles OutputGuardrailTripwireTriggered"]
    S5["5. Response Extraction\nParse BotResponse JSON\nExtract CTA flags, booking, email"]
    S6["6. Probing State Sync\nScore updates, question tracking"]
    S7["7. Negotiation State Sync\nProtected field enforcement"]
    S8["8. History Management\nSliding window: last 15 messages\nSummarize older messages"]
    S9["9. Executive Summary\nAsync via summarizer model"]
    S10["10. State Persistence\nsave_state → DB\nupdate_session → Semantic cache\nReturn BotState"]

    S1 --> S2 --> S3
    S3 -->|"Hit"| S3HIT
    S3 -->|"Miss"| S4
    S4 --> S5 --> S6 --> S7 --> S8 --> S9 --> S10
```

### Guardrail System

```mermaid
flowchart LR
    subgraph INPUT["Input Guardrail"]
        UM["User Message"] --> FP{"Fast-path\nregex match?"}
        FP -->|"Match"| SAFE["SAFE\nno LLM call"]
        FP -->|"No match"| LLM_IG["LLM guard\nnano model"]
        LLM_IG --> REC["RECORD\nnever blocks"]
    end

    subgraph OUTPUT["Output Guardrail"]
        RULES["12 rules\nvalidation"] --> APP{"approved?"}
        APP -->|"No"| SUGG["Use suggested_text"]
        APP -->|"Yes"| PASS["Pass through"]
    end
```

### Request Lifecycle

```mermaid
flowchart TD
    R1["1. HTTP Request\nBotRequest JSON"] --> R2["2. FastAPI validates via Pydantic"]
    R2 --> R3["3. convert_to_botstate\nMerge: UserContextRequest + session state + BotPersona"]
    R3 --> R4["4. run_chatbot_api - 10-step pipeline"]
    R4 --> R4A["4a. Load/create session"]
    R4A --> R4B["4b. Init probing + negotiation engines"]
    R4B --> R4C{"4c. Semantic cache check"}
    R4C -->|"HIT"| R4RET["Return cached"]
    R4C -->|"MISS"| R4D["4d. Execute agent graph"]

    subgraph AGENT_EXEC["Runner.run"]
        AG1["Input guardrail\nasync, record-only"] --> AG2["Main agent processes intent"]
        AG2 --> AG3["Handoff or tool call"]
        AG3 --> AG4["Child agent/tool executes"]
        AG4 --> AG5["Output guardrail\nasync, can block"]
        AG5 --> AG6["Return BotResponse"]
    end

    R4D --> AGENT_EXEC
    AGENT_EXEC --> R4E["4e. Sync probing state"]
    R4E --> R4F["4f. Sync negotiation state"]
    R4F --> R4G["4g. Update chat_history\nsliding window"]
    R4G --> R4H["4h. Generate executive summary"]
    R4H --> R4I["4i. Persist state +\nupdate semantic cache"]
    R4I --> R4J["4j. Return updated BotState"]
    R4J --> R5["5. Map BotState to APIResponse\nor full dict for /chat_ui"]
    R4RET --> R5
    R5 --> R6["6. HTTP Response JSON"]
```

### State Management (BotState)

```mermaid
flowchart TD
    BS["BotState\ncentral state object"]
    BS --> UC["user_context: UserContext\nuser_id, tenant_id, user_query\nchat_history, chat_summary\ncollected_fields, contact_details\nfollow_trigger, booking_confirmed\nlast_agent, ... 40+ fields"]
    BS --> BP["bot_persona: BotPersona\nname, company_name, industry\nproducts, assets, email_template\nworking_hours, rules\nprobing config, negotiation_config\n... 30+ fields"]
    BS --> PC["probing_context: ProbingContext\ntotal_score, probing_completed\ndetected_question_answer\ncan_show_cta"]
    BS --> OS["objection_state: ObjectionState\ncurrent_objection_count\nis_objection_limit_reached\nlimit_reach_count"]
    BS --> NS["negotiation_state: NegotiationState\nnegotiation_session\nnegotiation_attempts"]
    BS --> OT["response, input_guardrail_decision\nbrochure_flag, brochure_details\nhuman_requested, ..."]
```

### Deployment — Development

```mermaid
flowchart TD
    subgraph LOCAL["Local Machine"]
        UV["uvicorn main:app --reload"]
        UV --> SQ["SQLite - in-memory"]
        UV --> CH["ChromaDB - local"]
        UV --> API["Azure/OpenAI API calls"]
        ST["streamlit run streamlit_ui/app.py"]
        ST -->|"Connects to\nlocalhost:8000"| UV
    end
```

### Deployment — Production

```mermaid
flowchart LR
    LB["Load Balancer\nnginx/ALB"] --> APP["App Server\nuvicorn + gunicorn\nmain:app"]
    APP --> NEON["Neon PostgreSQL\nsessions"]
    APP --> AZURE["Azure OpenAI\nLLM calls"]
    APP --> QDRANT["Qdrant Cloud\nvector search"]
```

### Module Dependency Map

```mermaid
flowchart TD
    MAIN["main.py"] --> AA["app_agent.py"]

    AA --> FAC["app/agents/factory.py"]
    FAC --> DEF["app/agents/definitions.py"]
    DEF --> SALES["app/agents/sales/"]
    DEF --> BOOKING["app/agents/booking/"]
    DEF --> FOLLOWUP["app/agents/followup/"]
    DEF --> HUMAN["app/agents/human_escalation/"]
    DEF --> NEGO["app/agents/negotiation/"]
    DEF --> OBJ["app/agents/objection_handle/"]
    DEF --> EMAIL_A["app/agents/proceed_email/"]
    DEF --> LEAD["app/agents/lead_analysis/"]
    DEF --> BROCH["app/agents/brochure/"]
    DEF --> TMPL["app/agents/template_generation/"]
    FAC --> ACFG["app/agents/config.py"]
    ACFG --> ROUTE["app/route/route.py\nRouterModel, LiteLLM Router"]

    AA --> CORE["app/core/"]
    CORE --> MODELS["models.py - 60+ Pydantic models"]
    CORE --> GUARD["guardrail.py - input/output"]
    CORE --> PROBE["probing_state.py"]
    CORE --> NEGENG["negotiation.py"]
    CORE --> EXC["exceptions.py"]

    AA --> DB["app/database/"]
    DB --> SESSMGR["session_manager.py - SQLite"]
    DB --> PGMGR["postgresql_session_manager.py - Neon PG"]
    DB --> CACHE["cachememory.py - semantic cache"]
    DB --> SUMM["summarizer.py"]
    DB --> SLIDE["sliding_window.py"]
    DB --> EXECSUMM["executive_summary.py"]

    AA --> PROMPTS["app/prompts/\nall dynamic prompt generators"]
    AA --> UTILS["app/utils/\nprompt_cache.py, utils.py"]

    MAIN --> CFG["app/config/"]
    CFG --> SETTINGS["settings.py - env vars"]
    CFG --> CONST["constants.py - AgentName, defaults"]

    MAIN --> RAGMOD["rag/\nETL_Pipeline, Qdrant, retriever"]
    MAIN --> STUI["streamlit_ui/\napp.py, chat.py, persona.py, qa_panel.py"]
```

---

## From ARCHITECTURE_EVOLUTION.md

### Before vs After Architecture Comparison

```mermaid
flowchart TD
    subgraph BEFORE["BEFORE v1.0 - Simple Architecture"]
        B_API["API Request"] --> B_AGENT["Single Agent\nMonolithic"]
        B_AGENT --> B_STATE["Simple State\nDataclass"]
        B_AGENT --> B_LLM["Direct LLM Call\nSingle Provider"]
    end

    subgraph AFTER["AFTER v2.0 - Multi-Agent Architecture"]
        A_API["API Request"] --> A_PIPE["Input Guardrail → Root Agent → Output Guardrail"]
        A_PIPE --> A_SALES["Sales Agent"]
        A_PIPE --> A_DEMO["Demo Booking"]
        A_PIPE --> A_FOLLOW["Follow-up Agent"]
        A_SALES --> A_STATE["State Manager\nPersistent"]
        A_DEMO --> A_STATE
        A_FOLLOW --> A_STATE
        A_STATE --> A_INFRA["Pydantic Models • Semantic Cache • Summary"]
    end

    BEFORE -.->|"Evolution"| AFTER
```

### Exception Hierarchy (v2.0)

```mermaid
flowchart TD
    BRE["BotRunnerException\nbase"] --> CE["ConfigurationError"]
    BRE --> SE["StateError"]
    BRE --> AE["AgentError"]
    AE --> AEE["AgentExecutionError"]
    AE --> AHE["AgentHandoffError"]
    AE --> ATE["AgentTimeoutError"]
    BRE --> GE["GuardrailError"]
    GE --> IGE["InputGuardrailError"]
    GE --> OGE["OutputGuardrailError"]
    BRE --> TE["ToolError"]
    TE --> TEE["ToolExecutionError"]
    TE --> TVE["ToolValidationError"]
    BRE --> DBE["DatabaseError"]
    DBE --> DCE["ConnectionError"]
    DBE --> QE["QueryError"]
```

### Response Time Comparison

```mermaid
flowchart TD
    subgraph V1["v1.0 - No Optimization"]
        V1R["Request"] --> V1A["Agent"] --> V1L["LLM"] --> V1RES["Response\n2000-5000ms"]
    end

    subgraph V2["v2.0 - Optimized"]
        V2R["Request"] --> V2CACHE{"Cache Check\n50ms"}
        V2CACHE -->|"Hit"| V2HIT["Return cached\n100ms total"]
        V2CACHE -->|"Miss"| V2IG["Input Guardrail\n300ms"]
        V2IG -->|"Block"| V2BLK["Block attack\n400ms total"]
        V2IG -->|"Pass"| V2TRIAGE["Root Agent Triage\n200ms"]
        V2TRIAGE --> V2SPEC["Specialized Agent\n1000ms"]
        V2SPEC --> V2OG["Output Guardrail\n300ms"]
        V2OG --> V2RES["Response\n1500-2000ms typical"]
    end
```

---

## From AGENT_FLOWS.md

### System Overview (Main Agent Flow)

```mermaid
flowchart TD
    A["User Message"] --> B{"Input Guardrail"}
    B -->|"Matches SAFE_CONVERSATIONAL_PATTERNS"| C["Fast-path - no LLM"]
    B -->|"Otherwise"| D["LLM classification - record-only, never blocks"]
    C --> E["Main Agent - Triage"]
    D --> E

    E -->|"Handoff"| F["sales_agent\n(product/feature queries)"]
    E -->|"Handoff"| G["demo_booking_agent\n(book/reschedule/cancel)"]
    E -->|"Handoff"| H["followup_agent\n(reminders, follow-ups)"]
    E -->|"Handoff"| I["human_agent\n(escalation to live agent)"]

    E -->|"Tool call"| J["proceed_email\n(email switch)"]
    E -->|"Tool call"| K["negotiation_engine\n(pricing/discounts)"]
    E -->|"Tool call"| L["asset_sharing\n(brochures/docs)"]

    F --> M{"Output Guardrail"}
    G --> M
    H --> M
    I --> M
    J --> M
    K --> M
    L --> M

    M -->|"approved=no"| N["Use suggested_text fallback"]
    M -->|"guardrail error"| O["Fail-open - pass original"]
    M -->|"approved=yes"| P["API Response\n(BotResponse → APIResponse)"]
    N --> P
    O --> P
```

### Probing State Machine

```mermaid
flowchart TD
    A["Normal Probing"] --> B{"User Response Type"}
    B -->|"Answer"| C["score += value"]
    C --> D{"Threshold met?"}
    D -->|"Yes"| E["Show CTA"]
    E --> F["Booking handoff"]
    D -->|"No"| A

    B -->|"Objection"| G["objection_count++"]
    G --> H{"Limit reached?"}
    H -->|"Yes"| I["Show CTA"]
    I --> J{"Next message"}
    J --> K{"Reset cycle"}
    K -->|"reset count < limit"| L["Resume probing"]
    L --> A
    K -->|"reset count >= limit"| M["FREEZE\nCTA disabled, normal conversation"]
    H -->|"No"| A

    B -->|"Product query"| N["Answer via RAG"]
    N --> O["Re-ask current probing question"]
    O --> A
```

### Email Decision Tree

```mermaid
flowchart TD
    A["Email request detected"] --> B{"User email already in state?"}
    B -->|"Yes"| C["Match template"]
    C --> D["Generate HTML body"]
    D --> E["switch_to_email=True\nget_email_flag=True"]

    B -->|"No"| F["Ask for email"]
    F --> G["get_email_flag=False"]
    G --> H["User provides email in follow-up"]
    H --> I["Match template"]
    I --> J["Generate reply_body"]
    J --> K["switch_to_email=True\nget_email_flag=True"]
```

### Cross-Agent Workflow A: Probing → CTA → Booking

```mermaid
flowchart LR
    A1["main_agent\n(probing enabled)"] --> A2["Ask scored probing questions"]
    A2 --> A3["total_score reaches threshold"]
    A3 --> A4["Show CTA: Book a Demo"]
    A4 --> A5["User accepts"]
    A5 --> A6["Handoff to demo_booking_agent"]
    A6 --> A7["Collect email, datetime, product"]
    A7 --> A8["lead_analysis_tool classifies lead"]
```

### Cross-Agent Workflow B: Sales → Negotiation → Booking

```mermaid
flowchart LR
    B1["main_agent"] --> B2["Handoff to sales_agent"]
    B2 --> B3["User asks about pricing"]
    B3 --> B4["negotiation_engine tool called"]
    B4 --> B5["Negotiation rounds\ninitial → active → closing"]
    B5 --> B6["User satisfied with price"]
    B6 --> B7["Handoff to demo_booking_agent"]
    B7 --> B8["Products auto-selected\nfrom negotiation"]
```

### Cross-Agent Workflow C: Booking → Unavailable → Follow-up

```mermaid
flowchart LR
    C1["demo_booking_agent"] --> C2["Slot unavailable"]
    C2 --> C3["User can't find a good time"]
    C3 --> C4["Handoff to followup_agent"]
    C4 --> C5["Schedule follow-up reminder"]
```

### Cross-Agent Workflow D: Any Point → Human Escalation

```mermaid
flowchart LR
    D1["Any conversation point"] --> D2["User: Talk to someone"]
    D2 --> D3["Immediate handoff to human_agent"]
    D3 --> D4["Conversation context preserved\nin human_details"]
```

### Cross-Agent Workflow E: Sales → Objection → Asset Share → Booking

```mermaid
flowchart LR
    E1["main_agent"] --> E2["Handoff to sales_agent"]
    E2 --> E3["User asks about product"]
    E3 --> E4["User objects"]
    E4 --> E5["Objection handled empathetically"]
    E5 --> E6["proceed_with_asset_sharing"]
    E6 --> E7["Brochure/datasheet shared"]
    E7 --> E8["User: Let's book a demo"]
    E8 --> E9["Handoff to demo_booking_agent"]
```

---

## From PERSONA_GUIDE.md

### Persona to Agent Instruction Flow

```mermaid
flowchart TD
    BP["BotPersona JSON"] --> IG["instructions/generators.py\nConverts persona fields into\nnatural-language prompts"]
    IG --> MA["Main Agent\n• name\n• persona\n• rules\n• emoji"]
    IG --> SA["Sales Agent\n• products\n• USPs\n• features\n• offer"]
    IG --> BA["Booking Agent\n• working_hrs\n• contact_info"]
```

---

## From PRODUCTION_FEATURES.md

### LLM Fallback Chain

```mermaid
flowchart TD
    P["Primary\nOpenAI gpt-4.1"] -->|"failure"| F1["Fallback 1\nAzure gpt-4.1"]
    F1 -->|"failure"| F2["Fallback 2\nGemini gemini-3-flash"]
```

### Exception Hierarchy (Production)

```mermaid
flowchart TD
    BRE["BotRunnerException\nbase"] --> CE["ConfigurationError"]
    BRE --> SE["StateError"]
    SE --> SVE["StateValidationError"]
    BRE --> AE["AgentError"]
    AE --> AEE["AgentExecutionError"]
    AE --> AHE["AgentHandoffError"]
    AE --> ATE["AgentTimeoutError"]
    BRE --> GE["GuardrailError"]
    GE --> IGE["InputGuardrailError"]
    GE --> OGE["OutputGuardrailError"]
    BRE --> TE["ToolError"]
    TE --> TEE["ToolExecutionError"]
    TE --> TVE["ToolValidationError"]
    BRE --> DBE["DatabaseError"]
    DBE --> DCE["ConnectionError"]
    DBE --> QE["QueryError"]
    BRE --> ESE["ExternalServiceError"]
    ESE --> CAL["CalendlyAPIError"]
```
