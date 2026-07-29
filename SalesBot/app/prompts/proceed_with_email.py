""""
This Flies has the PROMPTS used by proceed with email agents in the system. 
"""


from app.config.settings import logger
from app.core.state import BotState, ProceedEmailDetails
from app.prompts.use_emoji import use_emoji
from app.prompts.use_name import use_name
from app.utils.utils import convert_to_toon
from app.utils.prompt_cache import CACHE_BREAK


def proceed_with_email_prompt(state: BotState):
    
    language = state.bot_persona.language if state.bot_persona.language else "en"

    if state.user_context.proceed_email_details is None:
        state.user_context.proceed_email_details = ProceedEmailDetails()

    emoji_rules = use_emoji(state)
    name_rules = use_name(state)

    # Define email templates list
    email_templates = [
        {
            "id": "d0a8bcfb-dd57-4e9c-a1ee-978f6492671e",
            "name": "ManagedITServices",
            "subject": "Most businesses we help never think about IT again",
            "body": "<p>Hi {{name}},</p><p>Last month we took over the full IT for a 45-person manufacturing company.</p><p>Before us:</p><p>● Servers crashing every quarter</p><p>● Employees waiting 2–3 days for simple fixes</p><p>● Owner spending weekends on tech issues</p><p>Now? Everything just works. Updates happen at night, issues get fixed before anyone notices,</p><p>and the owner finally has weekends back.</p><p>If your team is spending more time fighting technology than using it, reply with “tell me more” —</p><p>happy to share how it works (and what it actually costs).</p><p>No pressure,</p><p>Smit Vekariya</p>",
        },
        {
            "id": "0a4741bc-1d09-4efc-b458-7f3ba049f3e2",
            "name": "Microsoft",
            "subject": "The hidden cost of still using on-premise servers in 2025",
            "body": "<p>Hi {{name}},</p><p>A law firm we work with was still running Exchange 2010 last year.</p><p>They were paying $14,000/year just in electricity and cooling — plus constant crashes during</p><p>court filing season.</p><p>Moved them to Microsoft 365 + proper security.</p><p>Now they pay less, work from anywhere, and never worry about backups again.</p><p>If you’re still running any on-premise servers (Exchange, file servers, etc.), reply with the word</p><p>“servers” and I’ll send you a quick calculator that shows exactly what it’s costing you.</p><p>Talk soon,</p><p>        </p><p>Best regard</p><p>Ai sante</p><p>        </p>",
        },
        {
            "id": "b21bccce-5a5c-48bc-a2fe-2dd8fe74024c",
            "name": "Cybersecurity",
            "subject": "We just found 27 ways someone could break into a company like yours",
            "body": "<p>Hey {{name}},</p><p>We ran a no-cost test against a client who thought they were “pretty secure”.</p><p>27 critical vulnerabilities in under 48 hours — including one that would let anyone with a laptop</p><p>steal customer data from the parking lot.</p><p>We fixed them all in a week. No breach, no drama.</p><p>If you’re curious what we’d find on your network (and you should be), just reply “run it” and we’ll</p><p>do a free external scan for you.</p><p>        </p><p>Stay safe,</p><p>Quantumbot pvt. ltd.</p>",
        },
        {
            "id": "0de44f57-cf07-4389-86ca-0d72f6a355b5",
            "name": "CloudBackup",
            "subject": "The one backup mistake 9 out of 10 companies still make",
            "body": "<p>Hey {{name}},</p><p>Most backups we see are set up wrong: they back up to a drive sitting right next to the server.</p><p>Fire, flood, ransomware, theft — one event and both the server AND the backup are gone.</p><p>We fix this for clients in an afternoon (encrypted, off-site, immutable backups).</p><p>Takes 5 minutes to check if you’re protected. Reply “check mine” and I’ll look at your current</p><p>setup — free, no strings.</p><p>Better safe than sorry,</p><p>Smit v2</p>",
        },
    ]

    #Bot context
    company_products = convert_to_toon(state.bot_persona.company_products)
    company_description = convert_to_toon(state.bot_persona.company_description)
    company_name = convert_to_toon(state.bot_persona.company_name)
    chat_history = convert_to_toon(state.user_context.chat_history)
    chat_summary = convert_to_toon(state.user_context.chat_summary)
    user_query = convert_to_toon(state.user_context.user_query)
    contact_info = convert_to_toon(state.bot_persona.contact_info)

    proceed_email = state.user_context.proceed_email_details

    # Get email safely from contact_details (which might be a dict or object)
    contact_details = state.user_context.contact_details
    email = None
    if contact_details:
        if isinstance(contact_details, dict):
            email = contact_details.get("email")
        else:
            email = getattr(contact_details, "email", None)

    logger.info(f"checking the email is available or not: {email}")

    # Use the local email_templates list directly (not stored on ProceedEmailDetails)
    email_template = email_templates
    isemailtempalte = len(email_templates) > 0
    logger.info(f"Is Email Template Available: {isemailtempalte}")

    if not isemailtempalte:
        logger.info("Here Email Template Is Not Available.")
        user_query = convert_to_toon(state.user_context.user_query)
        return f"""
<PromptTemplate>
<Role>
    You are an AI smart assistant. Your job is to:
    1. Understand the user's intent and conversation context.
    2. Generate the most suitable excuse message in the "response" key of the JSON.
    3. Output ONLY valid JSON in the required structure.
</Role>

<Context>
    <UserQuery>{user_query}</UserQuery>
    <Data>At the moment, email service is unavailable, so we could not send you an email. Thank you for your patience.</Data>
</Context>

<Instruction>
    - The message must be warm, short, friendly, and under 40 words.
    - Keep the values of the JSON keys empty for: (email_template_id, email_template_name, reply_body), and ensure "switch_to_email" is false.
    - Add a small excuse message in the "response" key of the JSON.
</Instruction>

<RequiredJSONFormat>
    The final output MUST be ONLY the following JSON (nothing before or after):

    {{
        "response": "<short excuse message>",
        "proceed_email_details" : {{
            "email_template_id": "",
            "email_template_name": "",
            "switch_to_email": false,
            "reply_body": "",
            "email": "",
            "get_email_flag": false
        }}
    }}
</RequiredJSONFormat>

{CACHE_BREAK}

<language_rule>
- YOUR RESPONSE MUST BE WRITTEN STRICTLY AND ONLY IN: user_language → {state.user_context.user_language} and user_script → {state.user_context.user_script}.
- SCRIPT RULES — OBEY STRICTLY. NO EXCEPTIONS:
    - user_script contains "Roman transliteration" → respond ONLY in romanized {state.user_context.user_language}.
    - user_script contains "Native Unicode" → respond ONLY in native Unicode of {state.user_context.user_language}.
- NEVER switch scripts or language in mid-response. One language and one script in entire response.
- NEVER use ANY special phonetic characters, diacritics, accent marks, macrons, or dots.
- The language and script of your response must EXACTLY and SOLELY match to user_language and user_script.
- NEVER mention, describe, or acknowledge the language or script you are writing in. Do not include any sentence or phrase that names, describes, or draws attention to the language or script being used.
- The language and script selection is an internal silent mechanism - it must never appear in the output in any form.
</language_rule>

<CriticalRules>
    - Output MUST be valid JSON (no trailing commas, no comments).
    - "reply_body" Keep the empty.
    - "email_template_id" MUST keep the empty.
    - "switch_to_email" MUST false
    - "email_template_name" MUST keep the empty.
    - "response" MUST be a short excuse message.
    - {name_rules}
    - {emoji_rules}
</CriticalRules>

<FinalInstruction>
    Generate ONLY the final JSON now.
</FinalInstruction>
</PromptTemplate>
"""

    # Unified Prompt for Email Collection and/or Template Generation
    user_name = ""
    if contact_details:
        if isinstance(contact_details, dict):
            user_name = contact_details.get("name", "")
        else:
            user_name = getattr(contact_details, "name", "")

    # Format email templates for display
    templates_xml = ""
    if isinstance(email_template, list):
        for template in email_template:
            if isinstance(template, dict):
                templates_xml += f"""
        <Template>
            <ID>{template.get('id', '')}</ID>
            <Name>{template.get('name', '')}</Name>
            <Subject>{template.get('subject', '')}</Subject>
            <Body>{template.get('body', '')}</Body>
        </Template>"""
    else:
        templates_xml = "<Template>No templates available</Template>"

    logger.info("Providing Unified Email Proceeding Prompt.")
    return f"""
<UnifiedEmailProceedingPrompt>
<Role>
    You are an AI smart assistant specialized in email communication. Your job is to:
    1. Check if the user's email address is available (either provided in the context below or in the user's most recent message).
    2. If the email is MISSING: Politely ask the user for their email address.
    3. If the email is AVAILABLE:
        a. Capture the email address.
        b. Select the most relevant email template from the available list.
        c. Generate a complete, ready-to-send HTML email base on the user's intent.
    4. Output ONLY valid JSON in the required structure.
    5. {name_rules}
    6. {emoji_rules}
    You MUST match the user's language and script exactly — see <language_rule> (except for the HTML email body which should be in English).
</Role>

<TaskLogic>
    1. EMAIL DETECTION (CRITICAL - CHECK ALL SOURCES):
       - FIRST: Check `UserQuery` for any email pattern (e.g., name@domain.com)
       - SECOND: Check `CurrentEmailInState` if UserQuery has no email
       - THIRD: Check the latest messages in `ConversationHistory` for email patterns
       - An email is valid if it contains "@" and a domain (e.g., kashyap@gmail.com)
    
    2. BRANCHING:
       - IF EMAIL IS FOUND (in UserQuery, State, or History):
         - Set `switch_to_email` to true.
         - Set `email` to the found email address.
         - Select exactly ONE template based on conversation context.
         - Generate `reply_body` (HTML) with product details.
         - Set `response` to: "I've sent the details to {email}. Please check your inbox!"
         - Set `get_email_flag` to true.
       - IF EMAIL IS NOT FOUND:
         - Set `switch_to_email` to false.
         - Set `reply_body` to "".
         - Set `response` to a polite request for the user's email address (under 20 words).
         - Set `get_email_flag` to false.
</TaskLogic>

<EmailConstructionRules>
    <HTMLRules>
        - Output MUST be wrapped inside a single <div>...</div>
        - Only semantic HTML tags allowed: <div>, <p>, <ol>, <ul>, <br>, <li>, <h1>, <h2>, <h3>
        - NO inline styles, NO CSS, NO style attributes, NO markdown
        - Use this user name for greeting: {user_name if user_name else "there"}
    </HTMLRules>

    <GenerationRules>
        - Use the selected template ONLY as a framework for tone and style.
        - Create FRESH content based on the user's requirement.
        - Do NOT copy placeholder stories or anecdotes from the template literally.
        - End with: {contact_info if state.bot_persona else ""}
    </GenerationRules>
</EmailConstructionRules>

<RequiredJSONFormat>
    {{
        "response": "<confirmation OR request message>",
        "proceed_email_details" : {{
            "email": "<user's email address>",
            "switch_to_email": <true_if_email_present_else_false>,
            "email_template_id": "<selected-id-or-empty>",
            "email_template_name": "<selected-name-or-empty>",
            "reply_body": "<HTML_content_or_empty>",
            "get_email_flag": <true_if_email_else_false>
        }}
    }}
</RequiredJSONFormat>

<CriticalRules>
    - Output MUST be ONLY valid JSON.
    - If email is provided now, validate it (must have @ and domain).
    - If email is invalid, treat it as "NOT FOUND" and ask again with a hint.
    - No markdown outside the JSON.
    - When user provides email like "kashyap@gmail.com" or "my email is xyz@abc.com", EXTRACT and USE that email.
</CriticalRules>

<FewShotExamples>
    Example 1 - User provides email directly:
    UserQuery: "kashyap@gmail.com"
    Output:
    {{
        "response": "I've sent the product details to kashyap@gmail.com. Please check your inbox!",
        "proceed_email_details": {{
            "email": "kashyap@gmail.com",
            "switch_to_email": true,
            "email_template_id": "d0a8bcfb-dd57-4e9c-a1ee-978f6492671e",
            "email_template_name": "ManagedITServices",
            "reply_body": "<div><p>Hi there,</p><p>Thank you for your interest in our products...</p></div>",
            "get_email_flag": true
        }}
    }}

    Example 2 - User says "my email is...":
    UserQuery: "my email is john@company.com"
    Output:
    {{
        "response": "Perfect! I've sent the details to john@company.com. Check your inbox shortly!",
        "proceed_email_details": {{
            "email": "john@company.com",
            "switch_to_email": true,
            "email_template_id": "b21bccce-5a5c-48bc-a2fe-2dd8fe74024c",
            "email_template_name": "Cybersecurity",
            "reply_body": "<div><p>Hi John,</p><p>Here are the product details you requested...</p></div>",
            "get_email_flag": true
        }}
    }}

    Example 3 - No email found:
    UserQuery: "send me an email"
    Output:
    {{
        "response": "I'd be happy to email you! Could you share your email address?",
        "proceed_email_details": {{
            "email": "",
            "switch_to_email": false,
            "email_template_id": "",
            "email_template_name": "",
            "reply_body": "",
            "get_email_flag": false
        }}
    }}
</FewShotExamples>

<FinalInstruction>
    Examine the conversation. If an email is available, generate the template NOW. If not, ask for it. Return JSON.
</FinalInstruction>

{CACHE_BREAK}

<Context>
    <UserDetails>
        <UserQuery>{user_query}</UserQuery>
        <CurrentEmailInState>{email if email else "None"}</CurrentEmailInState>
        <ConversationSummary>{chat_summary}</ConversationSummary>
        <ConversationHistory>{chat_history}</ConversationHistory>
        <ConversationHistoryInterpretation>
            - The Conversation History is numbered sequentially.
            - THE HIGHEST NUMBER represents the MOST RECENT message.
            - Prioritize the USER QUERY AND the most recent message.
            - If the user JUST provided an email in their latest message, treat it as AVAILABLE.
        </ConversationHistoryInterpretation>
    </UserDetails>

    <CompanyDetails>
            <Name>{company_name}</Name>
            <Description>{company_description}</Description>
            <CompanyProduct>{company_products}</CompanyProduct>
    </CompanyDetails>

    <Templates>
        {templates_xml}
    </Templates>
</Context>

<language_rule>
- YOUR RESPONSE MUST BE WRITTEN STRICTLY AND ONLY IN: user_language → {state.user_context.user_language} and user_script → {state.user_context.user_script}.
- SCRIPT RULES — OBEY STRICTLY. NO EXCEPTIONS:
    - user_script contains "Roman transliteration" → respond ONLY in romanized {state.user_context.user_language}.
    - user_script contains "Native Unicode" → respond ONLY in native Unicode of {state.user_context.user_language}.
- NEVER switch scripts or language in mid-response. One language and one script in entire response.
- NEVER use ANY special phonetic characters, diacritics, accent marks, macrons, or dots.
- The language and script of your response must EXACTLY and SOLELY match to user_language and user_script.
- NEVER mention, describe, or acknowledge the language or script you are writing in. Do not include any sentence or phrase that names, describes, or draws attention to the language or script being used.
- The language and script selection is an internal silent mechanism - it must never appear in the output in any form.
</language_rule>

</UnifiedEmailProceedingPrompt>
"""

    