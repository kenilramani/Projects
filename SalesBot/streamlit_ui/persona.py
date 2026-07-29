"""
persona.py — Bot-persona definition & configuration dialog.
"""

from loguru import logger
import streamlit as st
import time
import math
import requests
from config import (
    GENERATE_PROBING_ENDPOINT,
    API_GENERATE_TIMEOUT,
    AUTOFILL_PERSONA_ENDPOINT,
    API_AUTOFILL_TIMEOUT,
    GENERATE_INSTRUCTIONS_ENDPOINT,
    GENERATE_TEMPLATES_ENDPOINT,
)
from database import save_user_persona, save_global_persona


# ---------------------------------------------------------------------------
# Default persona
# ---------------------------------------------------------------------------
def _clean_float(v, default=0.0):
    """Convert v to a finite float; replace NaN/Inf/None with *default*."""
    if v is None:
        return default
    try:
        f = float(v)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return default

def get_default_persona() -> dict:
    return {
        "name": "Apex Diabetes Agent",
        "industry": "Healthcare",
        "category": "Medical Clinic",
        "sub_category": "Diabetes & Thyroid Superspecialty",
        "business_type": "B2C",
        "company_name": "APEX DIABETES - THYROID SUPERSPECIALTY HORMONE CLINIC",
        "company_domain": "apexdiabetesthyroid.com",
        "company_description": "Apex Diabetes and Thyroid Clinic is a superspecialty hormone clinic in Rajkot, Gujarat, focused on diabetes, thyroid, PCOS, obesity, and metabolic health with a strong emphasis on patient education and wellness.",
        "company_products": [
            {
                "id": "e463a033-0c7f-4c8d-965a-063851b9e0f1",
                "name": "Diabetes Care",
                "description": "Comprehensive diagnosis, treatment, and long-term diabetes management.",
            },
            {
                "id": "e463a033-0c7f-4c8d-965a-063851b9e0f2",
                "name": "Thyroid Care",
                "description": "Specialized evaluation and treatment of thyroid disorders.",
            },
            {
                "id": "e463a033-0c7f-4c8d-965a-063851b9e0f3",
                "name": "PCOS / PCOD Treatment",
                "description": "Hormone-based treatment plans for PCOS and PCOD.",
            },
            {
                "id": "e463a033-0c7f-4c8d-965a-063851b9e0f4",
                "name": "Obesity Care",
                "description": "Medical weight management and metabolic health consultation.",
            },
            {
                "id": "e463a033-0c7f-4c8d-965a-063851b9e0f5",
                "name": "Full Body Checkup",
                "description": "Preventive metabolic screening through comprehensive blood tests.",
                "base_pricing": 0.0,
                "currency": "INR",
                "max_discount_percent": 0.0,
                "discount_strategy": "",
            },
        ],
        "core_usps": "Superspecialty hormone care, strong patient education focus, holistic wellness approach, and high patient satisfaction.",
        "core_features": "Online appointment booking, BMI calculator, patient education videos, wellness blogs, and specialty diabetes clinics.",
        "contact_info": "Rajkot, Gujarat | +91-9586605660",
        "language": "en, gu",
        "personality": "Professional, empathetic, calm, educational, and patient-friendly",
        "prompt": "You are a medical clinic assistant. Your role is to educate patients, understand their concerns, and guide them toward appropriate consultations without providing medical diagnosis or treatment advice.",
        "business_focus": "Endocrinology, diabetes management, thyroid care, and metabolic health",
        "goal_type": "appointment_booking",
        "use_emoji": False,
        "use_name_reference": False,
        "enable_probing": True,
        "probing_threshold": 40,
        "probing_questions_source": "guided",
        "rules": [
            "Do not provide medical diagnosis or prescriptions",
            "Ask gentle health-related questions one at a time",
            "Encourage doctor consultation for symptoms",
            "Maintain patient privacy and empathy",
            "CTA only after understanding patient concern",
        ],
        "objection_count_limit": 3,
        "current_cta": "Book an Appointment",
        "negotiation_config": {
            "currency": "INR",
        },
    }


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------
@st.dialog("⚙️ Configure Bot Persona", width="large")
def persona_config_dialog():
    cur = st.session_state.custom_persona or get_default_persona()

    tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "🌐 Autofill",
            "🎭 Identity",
            "🏢 Company",
            "🤖 Behaviour",
            "❓ Probing",
            "📝 Templates",
            "📦 Assets",
        ]
    )

    with tab0:
        _render_autofill_tab(cur)

    with tab1:
        _render_identity_tab(cur)

    with tab2:
        _render_company_tab(cur)

    with tab3:
        _render_behaviour_tab(cur)

    with tab4:
        _render_probing_tab(cur)

    with tab5:
        _render_templates_tab(cur)

    with tab6:
        _render_assets_tab(cur)

    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        if st.button("💾 Save Persona", type="primary", use_container_width=True):
            _commit_persona_silent()
            st.toast("Persona saved ✅")

    with c2:
        if st.button("🔄 Reset to Default", use_container_width=True):
            _reset_persona()


# ---------------------------------------------------------------------------
# TAB RENDERERS
# ---------------------------------------------------------------------------
def _render_autofill_tab(cur):
    """Render the Autofill from Website tab."""
    st.markdown("### 🌐 Autofill from Website")
    st.caption(
        "Enter a website URL to automatically extract company information and populate persona fields."
    )

    url = st.text_input(
        "Website URL", placeholder="https://example.com", key="_autofill_url"
    )

    st.markdown("**Advanced Settings**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        max_depth = st.number_input("Max Crawl Depth", 1, 5, 2, key="_autofill_depth")
    with c2:
        max_pages = st.number_input("Max Pages", 10, 100, 50, key="_autofill_pages")
    with c3:
        max_tokens = st.number_input(
            "Max Tokens", 10000, 50000, 30000, step=5000, key="_autofill_tokens"
        )
    with c4:
        max_products = st.number_input(
            "Max Products", 1, 20, 5, key="_autofill_products"
        )

    st.divider()

    if st.button("🌐 Autofill from Website", type="primary", use_container_width=True):
        if url:
            _run_autofill(url, max_depth, max_pages, max_tokens, max_products)
        else:
            st.warning("Please enter a URL")

    st.info(
        "💡 After autofill, switch to other tabs to review and edit the extracted information."
    )


def _render_identity_tab(cur):
    st.session_state._pd_name = st.text_input("Bot Name", cur.get("name", ""))

    st.divider()

    st.session_state._pd_personality = st.text_input(
        "Personality", cur.get("personality", "")
    )
    st.session_state._pd_goal_type = st.text_input(
        "Goal Type", cur.get("goal_type", "")
    )
    st.session_state._pd_language = st.text_input("Language", cur.get("language", "en"))
    st.session_state._pd_current_cta = st.text_input(
        "Current CTA", cur.get("current_cta", "")
    )

    st.session_state._pd_use_emoji = st.toggle("Use Emoji", cur.get("use_emoji", True))
    st.session_state._pd_use_name_reference = st.toggle(
        "Use Name Reference", cur.get("use_name_reference", True)
    )
    st.session_state._pd_enable_probing = st.toggle(
        "Enable Probing", cur.get("enable_probing", True)
    )

    st.session_state._pd_probing_threshold = st.number_input(
        "Probing Threshold", 0, 100, cur.get("probing_threshold", 50)
    )

    st.session_state._pd_objection_count = st.number_input(
        "Objection Count Limit",
        1,
        10,
        max(1, min(10, cur.get("objection_count_limit") or 3)),
    )


def _render_company_tab(cur):
    st.session_state._pd_company_name = st.text_input(
        "Company Name", cur.get("company_name", "")
    )
    st.session_state._pd_company_domain = st.text_input(
        "Company Domain", cur.get("company_domain", "")
    )
    st.session_state._pd_contact_info = st.text_input(
        "Contact Info", cur.get("contact_info", "")
    )
    st.session_state._pd_offer_desc = st.text_input(
        "Offer Description", cur.get("offer_description", "")
    )

    # Initialize negotiation config in session state if not present (moved from Negotiation Tab)
    if "_pd_negotiation_config" not in st.session_state:
        neg_config = cur.get("negotiation_config", {})
        st.session_state._pd_negotiation_config = {
            "currency": neg_config.get("currency", "INR"),
        }
    
    nc = st.session_state._pd_negotiation_config
    nc["currency"] = st.text_input(
        "Currency Symbol/Code", 
        value=nc["currency"],
        help="e.g. $, INR, ₹, INR"
    )

    st.divider()
    st.subheader("Business Classification")

    st.session_state._pd_industry = st.text_input("Industry", cur.get("industry", ""))
    st.session_state._pd_category = st.text_input("Category", cur.get("category", ""))
    st.session_state._pd_sub_category = st.text_input(
        "Sub-category", cur.get("sub_category", "")
    )
    st.session_state._pd_business_type = st.text_input(
        "Business Type", cur.get("business_type", "")
    )
    st.session_state._pd_business_focus = st.text_input(
        "Business Focus", cur.get("business_focus", "")
    )

    st.divider()

    st.session_state._pd_company_desc = st.text_area(
        "Company Description", cur.get("company_description", ""), height=100
    )

    st.session_state._pd_core_usps = st.text_area(
        "Core USPs (Unique Selling Points)", cur.get("core_usps", ""), height=80
    )

    st.session_state._pd_core_features = st.text_area(
        "Core Features", cur.get("core_features", ""), height=80
    )

    st.divider()
    st.subheader("Company Products/Services")
    st.caption(
        "Define your company's products/services. Each product has an ID, name, and description."
    )

    products_list = cur.get("company_products", []) or []

    # Display existing products in editable format
    if products_list and isinstance(products_list, list) and len(products_list) > 0:
        products_data = []
        for i, p in enumerate(products_list):
            if isinstance(p, dict):
                products_data.append(
                    {
                        "ID": p.get("id", f"prod_{i+1:03d}"),
                        "Name": p.get("name", ""),
                        "Description": p.get("description", ""),
                        "Base Pricing": p.get("base_pricing"),
                        "Currency": p.get("currency", "INR"),
                        "Max Discount %": p.get("max_discount_percent", 0.0),
                        "Discount Strategy": p.get("discount_strategy", ""),
                    }
                )

        if products_data:
            edited_products = st.data_editor(
                products_data,
                num_rows="dynamic",
                use_container_width=True,
                key="products_editor",
                column_config={
                    "ID": st.column_config.TextColumn("ID", width=80),
                    "Name": st.column_config.TextColumn("Name", width=150),
                    "Description": st.column_config.TextColumn(
                        "Description", width=400
                    ),
                },
            )
            st.session_state._pd_products_data = edited_products
        else:
            edited_products = st.data_editor(
                [{"ID": "prod_001", "Name": "", "Description": ""}],
                num_rows="dynamic",
                use_container_width=True,
                key="products_editor",
                column_config={
                    "ID": st.column_config.TextColumn("ID", width=80),
                    "Name": st.column_config.TextColumn("Name", width=150),
                    "Description": st.column_config.TextColumn("Description", width=300),
                    "Base Pricing": st.column_config.NumberColumn(
                        "Base Price", min_value=0, step=0.01, format="%.2f"
                    ),
                    "Currency": st.column_config.TextColumn("Currency", width=80),
                    "Max Discount %": st.column_config.NumberColumn(
                        "Max Disc %", min_value=0, max_value=100, step=1
                    ),
                    "Discount Strategy": st.column_config.TextColumn(
                        "Discount Strategy", width=150
                    ),
                },
            )
            st.session_state._pd_products_data = edited_products
    else:
        # Fallback to default products if current persona has none
        default_persona = get_default_persona()
        default_products = default_persona.get("company_products", []) or []

        if (
            default_products
            and isinstance(default_products, list)
            and len(default_products) > 0
        ):
            products_data = []
            for i, p in enumerate(default_products):
                if isinstance(p, dict):
                    products_data.append(
                        {
                            "ID": p.get("id", f"prod_{i+1:03d}"),
                            "Name": p.get("name", ""),
                            "Description": p.get("description", ""),
                            "Base Pricing": p.get("base_pricing"),
                            "Max Discount %": p.get("max_discount_percent", 0.0),
                        }
                    )
            edited_products = st.data_editor(
                products_data,
                num_rows="dynamic",
                use_container_width=True,
                key="products_editor",
                column_config={
                    "ID": st.column_config.TextColumn("ID", width=80),
                    "Name": st.column_config.TextColumn("Name", width=150),
                    "Description": st.column_config.TextColumn(
                        "Description", width=400
                    ),
                    "Base Pricing": st.column_config.NumberColumn(
                        "Base Price", min_value=0.0, step=0.01, format="%.2f"
                    ),
                    "Max Discount %": st.column_config.NumberColumn(
                        "Max Disc %", min_value=0.0, max_value=100.0, step=0.5
                    ),
                },
            )
        else:
            st.info("No products defined. Add products below.")
            edited_products = st.data_editor(
                [
                    {
                        "ID": "prod_001",
                        "Name": "",
                        "Description": "",
                        "Base Pricing": 0.0,
                        "Max Discount %": 0.0
                    }
                ],
                num_rows="dynamic",
                use_container_width=True,
                key="products_editor",
                column_config={
                    "ID": st.column_config.TextColumn("ID", width=80),
                    "Name": st.column_config.TextColumn("Name", width=150),
                    "Description": st.column_config.TextColumn(
                        "Description", width=400
                    ),
                    "Base Pricing": st.column_config.NumberColumn(
                        "Base Price", min_value=0.0, step=0.01, format="%.2f"
                    ),
                    "Max Discount %": st.column_config.NumberColumn(
                        "Max Disc %", min_value=0.0, max_value=100.0, step=0.5
                    ),
                },
            )
        st.session_state._pd_products_data = edited_products

    # Working Hours Section
    st.divider()
    st.subheader("Working Hours")
    st.caption("Configure working hours for each day of the week.")

    default_working_hours = [
        {
            "Day": "Monday",
            "Type": "Working",
            "Start Time": "10:00",
            "End Time": "19:00",
        },
        {
            "Day": "Tuesday",
            "Type": "Working",
            "Start Time": "10:00",
            "End Time": "19:00",
        },
        {
            "Day": "Wednesday",
            "Type": "Working",
            "Start Time": "10:00",
            "End Time": "19:00",
        },
        {
            "Day": "Thursday",
            "Type": "Working",
            "Start Time": "10:00",
            "End Time": "19:00",
        },
        {
            "Day": "Friday",
            "Type": "Working",
            "Start Time": "10:00",
            "End Time": "19:00",
        },
        {"Day": "Saturday", "Type": "Holiday", "Start Time": "", "End Time": ""},
        {"Day": "Sunday", "Type": "Holiday", "Start Time": "", "End Time": ""},
    ]

    working_hours_list = cur.get("working_hours", []) or []
    if working_hours_list and isinstance(working_hours_list, list):
        hours_data = []
        for wh in working_hours_list:
            if isinstance(wh, dict):
                hours_data.append(
                    {
                        "Day": wh.get("day", ""),
                        "Type": wh.get("type", "Working"),
                        "Start Time": wh.get("start_time", "") or "",
                        "End Time": wh.get("end_time", "") or "",
                    }
                )
        if not hours_data:
            hours_data = default_working_hours
    else:
        hours_data = default_working_hours

    edited_hours = st.data_editor(
        hours_data,
        use_container_width=True,
        key="working_hours_editor",
        column_config={
            "Day": st.column_config.SelectboxColumn(
                "Day",
                options=[
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ],
                width=100,
            ),
            "Type": st.column_config.SelectboxColumn(
                "Type", options=["Working", "Holiday"], width=80
            ),
            "Start Time": st.column_config.TextColumn("Start Time", width=80),
            "End Time": st.column_config.TextColumn("End Time", width=80),
        },
    )
    st.session_state._pd_working_hours_data = edited_hours

    # Company Management Section
    st.divider()
    st.subheader("Company Management")
    st.caption("Add key contacts/executives for escalation or reference.")

    management_list = cur.get("company_management", []) or []
    if management_list and isinstance(management_list, list):
        mgmt_data = []
        for m in management_list:
            if isinstance(m, dict):
                mgmt_data.append(
                    {
                        "Name": m.get("name", ""),
                        "Designation": m.get("designation", ""),
                        "Email": m.get("email", ""),
                        "Phone": m.get("phone_number", ""),
                    }
                )
        if not mgmt_data:
            mgmt_data = [{"Name": "", "Designation": "", "Email": "", "Phone": ""}]
    else:
        mgmt_data = [{"Name": "", "Designation": "", "Email": "", "Phone": ""}]

    edited_mgmt = st.data_editor(
        mgmt_data,
        num_rows="dynamic",
        use_container_width=True,
        key="management_editor",
        column_config={
            "Name": st.column_config.TextColumn("Name", width=120),
            "Designation": st.column_config.TextColumn("Designation", width=120),
            "Email": st.column_config.TextColumn("Email", width=150),
            "Phone": st.column_config.TextColumn("Phone", width=120),
        },
    )
    st.session_state._pd_management_data = edited_mgmt


def _render_behaviour_tab(cur):
    st.session_state._pd_prompt = st.text_area(
        "System Prompt", cur.get("prompt", ""), height=140
    )

    rules = cur.get("rules", [])
    st.session_state._pd_rules = st.text_area(
        "Rules (one per line)", "\n".join(rules), height=120
    )


def _render_probing_tab(cur):
    st.markdown("### Probing Questions")

    rows = [
        {
            "ID": q.get("id"),
            "Question": q.get("question"),
            "Score": q.get("score", 10.0),
            "Priority": q.get("priority", i + 1),
            "Mandatory": q.get("mandatory", False),
        }
        for i, q in enumerate(cur.get("probing_questions", []))
    ] or [
        {"ID": "q_1", "Question": "", "Score": 10.0, "Priority": 1, "Mandatory": False}
    ]

    if "_pd_questions_editor" not in st.session_state:
        st.session_state._pd_questions_editor = rows

    st.session_state._pd_questions_editor = st.data_editor(
        st.session_state._pd_questions_editor,
        num_rows="dynamic",
        use_container_width=True,
    )

    st.divider()

    # Instructions Suggestions Section
    st.markdown("### 💡 Instruction Suggestions")
    st.caption(
        "Generate AI-powered instruction suggestions based on your persona, then select one to use."
    )

    # Initialize session state for instructions
    if "_pd_instruction_suggestions" not in st.session_state:
        st.session_state._pd_instruction_suggestions = []

    col_inst1, col_inst2 = st.columns([3, 1])
    with col_inst1:
        if st.button("✨ Generate Instruction Suggestions", use_container_width=True):
            max_inst = st.session_state.get("_pd_max_instructions", 5)
            _generate_instruction_suggestions(max_inst)
    with col_inst2:
        st.session_state._pd_max_instructions = st.number_input(
            "Max", min_value=1, max_value=10, value=5, key="_inst_max_input"
        )

    # Display dropdown if suggestions are available
    if st.session_state._pd_instruction_suggestions:
        selected_instruction = st.selectbox(
            "Select an instruction to use:",
            options=st.session_state._pd_instruction_suggestions,
            key="_pd_selected_instruction",
        )
    else:
        st.info(
            "Click 'Generate Instruction Suggestions' to get AI-powered suggestions based on your persona."
        )
        selected_instruction = None

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        total_k = st.number_input("How many?", 1, 20, 5)
    with c2:
        # Use selected instruction as default if available
        default_comment = st.session_state.get("_pd_selected_instruction", "") or ""
        comment = st.text_area("Instructions", value=default_comment, height=70)

    if st.button("🔮 Generate", use_container_width=True):
        _generate_probing_questions(total_k, comment)





def _render_templates_tab(cur):
    """Render the Templates tab with editable fields, Add Variable and Add Button."""
    st.markdown("### 📝 WhatsApp Templates")
    st.caption(
        "Auto-generated WhatsApp message templates for your products. Edit and save with the Save Persona button."
    )

    # Initialize templates in session state
    if "_pd_templates_data" not in st.session_state:
        st.session_state._pd_templates_data = cur.get("templates", []) or []

    templates = st.session_state._pd_templates_data

    # Generate Templates Section
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("✨ Generate Templates", type="primary", use_container_width=True):
            max_prods = st.session_state.get("_pd_template_max_products", 5)
            _generate_templates(max_prods)
    with col2:
        st.session_state._pd_template_max_products = st.number_input(
            "Max Products",
            min_value=1,
            max_value=20,
            value=5,
            key="_template_max_input",
        )

    st.divider()

    if templates:
        # Create dropdown with template names
        template_names = [
            t.get("name", f"Template {i+1}") for i, t in enumerate(templates)
        ]

        selected_name = st.selectbox(
            "Select Template", options=template_names, key="_pd_selected_template_name"
        )

        # Find selected template
        selected_idx = (
            template_names.index(selected_name)
            if selected_name in template_names
            else 0
        )
        selected_template = (
            templates[selected_idx] if selected_idx < len(templates) else None
        )

        if selected_template:
            st.markdown("---")

            # Template Details Section
            st.markdown("#### Template Details")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                new_name = st.text_input(
                    "Template Name*",
                    value=selected_template.get("name", ""),
                    key=f"_tpl_name_{selected_idx}",
                )
                templates[selected_idx]["name"] = new_name
            with c2:
                category_options = ["Utility", "Marketing"]
                current_cat = selected_template.get("category", "Utility")
                cat_idx = (
                    category_options.index(current_cat)
                    if current_cat in category_options
                    else 0
                )
                new_cat = st.selectbox(
                    "Category*",
                    options=category_options,
                    index=cat_idx,
                    key=f"_tpl_cat_{selected_idx}",
                )
                templates[selected_idx]["category"] = new_cat
            with c3:
                lang_options = [
                    "English",
                    "Hindi",
                    "Gujarati",
                    "Spanish",
                    "French",
                    "German",
                ]
                current_lang = selected_template.get("language", "English")
                lang_idx = (
                    lang_options.index(current_lang)
                    if current_lang in lang_options
                    else 0
                )
                new_lang = st.selectbox(
                    "Language*",
                    options=lang_options,
                    index=lang_idx,
                    key=f"_tpl_lang_{selected_idx}",
                )
                templates[selected_idx]["language"] = new_lang
            with c4:
                header_options = ["Text", "Image", "Video", "Document"]
                current_header = selected_template.get("header_type", "Text")
                header_idx = (
                    header_options.index(current_header)
                    if current_header in header_options
                    else 0
                )
                new_header = st.selectbox(
                    "Header Type*",
                    options=header_options,
                    index=header_idx,
                    key=f"_tpl_header_{selected_idx}",
                )
                templates[selected_idx]["header_type"] = new_header

            # Message Content Section
            st.markdown("#### Message Content")

            # Body and Preview side by side
            body_edit_col, body_preview_col = st.columns(2)

            with body_edit_col:
                st.markdown("**BODY***")
                body = selected_template.get("body", "")
                new_body = st.text_area(
                    "Body",
                    value=body,
                    height=200,
                    key=f"_tpl_body_{selected_idx}",
                    label_visibility="collapsed",
                )
                templates[selected_idx]["body"] = new_body

            with body_preview_col:
                st.markdown("**BODY PREVIEW**")
                preview_body = templates[selected_idx].get("body", "")
                preview_variables = templates[selected_idx].get("variables", []) or []

                # Substitute variables in preview (handle both {1} and {{1}} formats)
                for i, var_value in enumerate(preview_variables):
                    # Handle double braces {{1}}
                    double_brace_placeholder = f"{{{{{i+1}}}}}"
                    preview_body = preview_body.replace(
                        double_brace_placeholder, f"{var_value}"
                    )
                    # Handle single braces {1}
                    single_brace_placeholder = f"{{{i+1}}}"
                    preview_body = preview_body.replace(
                        single_brace_placeholder, f"{var_value}"
                    )

                # Display preview with preserved newlines in a styled container
                if preview_body:
                    # Convert newlines to <br> for proper display and wrap in a styled div
                    preview_html = preview_body.replace("\n", "<br>")
                    st.markdown(
                        f"""<div style="background-color: rgba(255,255,255,0.05); border-radius: 8px; padding: 12px; min-height: 180px; border: 1px solid rgba(255,255,255,0.1);">{preview_html}</div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        """<div style="background-color: rgba(255,255,255,0.05); border-radius: 8px; padding: 12px; min-height: 180px; border: 1px solid rgba(255,255,255,0.1); color: rgba(255,255,255,0.5);"><em>No body content</em></div>""",
                        unsafe_allow_html=True,
                    )

            # Variables Section
            st.markdown("**VARIABLES**")
            variables = selected_template.get("variables", []) or []

            # Track which variables to delete
            vars_to_delete = []

            if variables:
                for i, var in enumerate(variables):
                    var_col1, var_col2, var_col3 = st.columns([2, 4, 1])
                    with var_col1:
                        st.markdown(f"**Variable {{{{{i+1}}}}}***")
                    with var_col2:
                        new_var = st.text_input(
                            f"Value for {{{{{i+1}}}}}",
                            value=var,
                            key=f"_tpl_var_{selected_idx}_{i}",
                            label_visibility="collapsed",
                            placeholder=f"Enter value for {{{{{i+1}}}}}",
                        )
                        templates[selected_idx]["variables"][i] = new_var
                    with var_col3:
                        if st.button("🗑️", key=f"_del_var_{selected_idx}_{i}"):
                            vars_to_delete.append(i)

            # Process variable deletions after the loop (to avoid index issues)
            if vars_to_delete:
                for idx in sorted(vars_to_delete, reverse=True):
                    templates[selected_idx]["variables"].pop(idx)
                st.session_state._pd_templates_data = templates
                st.toast(f"Deleted {len(vars_to_delete)} variable(s) 🗑️")

            # Add Variable button
            if st.button(
                "+ Add Variable",
                key=f"_add_var_{selected_idx}",
                use_container_width=False,
            ):
                variables = templates[selected_idx].get("variables", []) or []
                new_var_num = len(variables) + 1
                variables.append(f"Variable {new_var_num}")
                templates[selected_idx]["variables"] = variables
                # Add placeholder to body
                current_body = templates[selected_idx].get("body", "")
                templates[selected_idx]["body"] = (
                    current_body + f" {{{{{new_var_num}}}}}"
                )
                # Update session state directly without rerun
                st.session_state._pd_templates_data = templates
                st.toast(f"Added variable {{{{{new_var_num}}}}} to body ✅")

            # Footer
            st.markdown("**FOOTER (OPTIONAL)**")
            footer = selected_template.get("footer", "To OPT Out, type STOP")
            new_footer = st.text_input(
                "Footer",
                value=footer,
                key=f"_tpl_footer_{selected_idx}",
                label_visibility="collapsed",
                placeholder="To OPT Out, type STOP",
            )
            templates[selected_idx]["footer"] = new_footer

            # Buttons Section
            st.markdown("#### Buttons")
            buttons = selected_template.get("buttons", []) or []

            # Track which buttons to delete
            btns_to_delete = []

            for i, btn in enumerate(buttons):
                btn_type = (
                    btn.get("button_type", "Url") if isinstance(btn, dict) else "Url"
                )
                btn_text = (
                    btn.get("button_text", "") if isinstance(btn, dict) else str(btn)
                )

                btn_col1, btn_col2, btn_col3 = st.columns([2, 3, 1])
                with btn_col1:
                    type_options = ["Url", "Quick Reply", "Phone Number"]
                    type_idx = (
                        type_options.index(btn_type) if btn_type in type_options else 0
                    )
                    new_btn_type = st.selectbox(
                        f"Button Type",
                        options=type_options,
                        index=type_idx,
                        key=f"_tpl_btn_type_{selected_idx}_{i}",
                    )
                    templates[selected_idx]["buttons"][i]["button_type"] = new_btn_type
                with btn_col2:
                    new_btn_text = st.text_input(
                        f"Button Text",
                        value=btn_text,
                        key=f"_tpl_btn_text_{selected_idx}_{i}",
                        placeholder="Enter button text",
                    )
                    templates[selected_idx]["buttons"][i]["button_text"] = new_btn_text
                with btn_col3:
                    st.markdown("")  # Spacer for alignment
                    if st.button("🗑️", key=f"_del_btn_{selected_idx}_{i}"):
                        btns_to_delete.append(i)

            # Process button deletions after the loop
            if btns_to_delete:
                for idx in sorted(btns_to_delete, reverse=True):
                    templates[selected_idx]["buttons"].pop(idx)
                st.session_state._pd_templates_data = templates
                st.toast(f"Deleted {len(btns_to_delete)} button(s) 🗑️")

            # Add Button row
            add_btn_col1, add_btn_col2, add_btn_col3 = st.columns([2, 3, 1])
            with add_btn_col1:
                new_btn_type_add = st.selectbox(
                    "Button Type",
                    options=["Url", "Quick Reply", "Phone Number"],
                    key=f"_new_btn_type_{selected_idx}",
                )
            with add_btn_col2:
                new_btn_text_add = st.text_input(
                    "Button Text",
                    key=f"_new_btn_text_{selected_idx}",
                    placeholder="Enter button text",
                )
            with add_btn_col3:
                st.markdown("")  # Spacer for alignment
                if st.button("+ Add Button", key=f"_add_btn_{selected_idx}"):
                    if not templates[selected_idx].get("buttons"):
                        templates[selected_idx]["buttons"] = []
                    templates[selected_idx]["buttons"].append(
                        {
                            "button_type": new_btn_type_add,
                            "button_text": new_btn_text_add,
                        }
                    )
                    st.session_state._pd_templates_data = templates
                    st.toast("Added new button ✅")

        st.divider()
        st.info(
            f"📊 Total Templates: {len(templates)} | Templates are saved with your persona in the database."
        )
    else:
        st.info(
            "💡 No templates generated yet. Click 'Generate Templates' to create WhatsApp templates based on your products."
        )


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _generate_probing_questions(total_k: int, comment: str):
    with st.spinner("Generating questions…"):
        # Collect previously generated questions from the editor
        existing_questions = st.session_state.get("_pd_questions_editor", [])
        prev_questions_list = [
            q.get("Question", "") for q in existing_questions if q.get("Question")
        ]

        # # Build the final comment with previous questions appended
        # final_comment = comment or ""
        # if prev_questions_list:
        #     prev_questions_text = "; ".join(prev_questions_list)
        #     final_comment += f"\n\nPreviously generated questions (do NOT repeat these): {prev_questions_text}"
        logger.info(f"Generating {total_k} questions with comment: {comment}")
        payload = {
            "custom_persona": st.session_state.custom_persona,
            "total_k": total_k,
            "comment": comment.strip() if comment else "",
        }

        resp = requests.post(
            GENERATE_PROBING_ENDPOINT,
            json=payload,
            timeout=API_GENERATE_TIMEOUT,
        )
        if resp.status_code != 200:
            st.error("Failed to generate questions")
            return

        data = resp.json()
        questions = data if isinstance(data, list) else data.get("questions", [])

        st.session_state._pd_questions_editor = [
            {
                "ID": q.get("id", f"q_{i+1}"),
                "Question": q.get("question", ""),
                "Score": q.get("score", 10.0),
                "Priority": q.get("priority", i + 1),
                "Mandatory": q.get("mandatory", False),
            }
            for i, q in enumerate(questions)
        ]

        _commit_persona_silent()
        st.success(f"Generated & auto-saved {len(questions)} questions ✅")


def _generate_templates(max_products: int = 5):
    """Generate WhatsApp templates based on current persona products."""
    with st.spinner("Generating templates..."):
        try:
            payload = {
                "custom_persona": st.session_state.custom_persona,
                "max_products": max_products,
            }

            resp = requests.post(
                GENERATE_TEMPLATES_ENDPOINT,
                json=payload,
                timeout=API_GENERATE_TIMEOUT,
            )

            if resp.status_code != 200:
                st.error(f"Failed to generate templates: {resp.status_code}")
                return

            data = resp.json()
            # Extract templates list from response
            templates = data.get("templates", [])

            if templates:
                st.session_state._pd_templates_data = templates
                _commit_persona_silent()
                st.success(f"Generated & auto-saved {len(templates)} templates ✅")
            else:
                st.warning(
                    "No templates were generated. Make sure you have products defined in your persona."
                )

        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error generating templates: {e}")
            st.error(f"Error: {e}")


def _render_assets_tab(cur):
    """Render the Assets tab — lets users add/edit/delete shareable assets."""
    import uuid as _uuid

    st.markdown("### 📦 Shareable Assets")
    st.caption(
        "Define assets (brochures, PDFs, documents, files) that the bot can share "
        "with users during conversations. These are automatically injected into "
        "the agent's context."
    )

    # Initialize assets in session state from persona
    if "_pd_assets_data" not in st.session_state:
        raw = cur.get("assets", []) or []
        st.session_state._pd_assets_data = [
            {
                "ID": a.get("asset_id", ""),
                "Name": a.get("asset_name", ""),
                "Path / URL": a.get("asset_path", ""),
                "Description": a.get("asset_description", ""),
                "Asset Type": a.get("asset_type", ""),
                "Other Info": a.get("other_info", ""),
            }
            for a in raw
        ] if raw else []

    assets_list = st.session_state._pd_assets_data

    # ── Add New Asset form ────────────────────────────────────────────────
    st.markdown("#### ➕ Add New Asset")
    with st.form("add_asset_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("Asset Name *", placeholder="Product Brochure Q1")
        with c2:
            new_path = st.text_input(
                "Path / URL",
                placeholder="/uploads/brochure_q1.pdf  or  https://...",
            )
        new_desc = st.text_area(
            "Description", placeholder="Q1 2025 product overview brochure", height=80
        )
        new_type = st.text_input(
            "Asset Type (optional)",
            placeholder="PDF, Image, Video, etc.",
        )
        new_info = st.text_area(
            "Other Info (optional)",
            placeholder="Target: enterprise clients, Language: English",
            height=60,
        )

        # File uploader (stores filename; actual file handling is outside scope)
        uploaded_file = st.file_uploader(
            "Or upload a file (PDF, PNG, JPG, DOCX, etc.)",
            type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx", "pptx", "csv", "txt"],
        )

        submitted = st.form_submit_button("📎 Add Asset", use_container_width=True)
        if submitted:
            if not new_name.strip():
                st.warning("Asset Name is required.")
            else:
                asset_id = str(_uuid.uuid4())[:8]
                # If user uploaded a file, store its name as path hint
                path_value = new_path.strip()
                if uploaded_file and not path_value:
                    path_value = f"[uploaded] {uploaded_file.name}"

                assets_list.append(
                    {
                        "ID": asset_id,
                        "Name": new_name.strip(),
                        "Path / URL": path_value,
                        "Description": new_desc.strip(),
                        "Asset Type": new_type.strip(),
                        "Other Info": new_info.strip(),
                    }
                )
                st.session_state._pd_assets_data = assets_list
                _commit_persona_silent()
                st.toast(f"Added asset: {new_name.strip()} ✅")
                st.rerun()

    st.divider()

    # ── Display existing assets ───────────────────────────────────────────
    if assets_list:
        st.markdown(f"#### Existing Assets ({len(assets_list)})")

        indices_to_delete = []
        for i, asset in enumerate(assets_list):
            with st.expander(
                f"📄 {asset.get('Name', 'Untitled')}  (ID: {asset.get('ID', '?')})",
                expanded=False,
            ):
                ac1, ac2 = st.columns([4, 1])
                with ac1:
                    st.markdown(f"**Description:** {asset.get('Description', '—')}")
                    st.markdown(f"**Path / URL:** `{asset.get('Path / URL', '—')}`")
                    if asset.get("Other Info"):
                        st.markdown(f"**Other Info:** {asset.get('Other Info')}")
                with ac2:
                    if st.button("🗑️ Delete", key=f"_del_asset_{i}"):
                        indices_to_delete.append(i)

        if indices_to_delete:
            for idx in sorted(indices_to_delete, reverse=True):
                assets_list.pop(idx)
            st.session_state._pd_assets_data = assets_list
            _commit_persona_silent()
            st.toast(f"Deleted {len(indices_to_delete)} asset(s) 🗑️")
            st.rerun()
    else:
        st.info(
            "No assets added yet. Use the form above to add brochures, documents, "
            "or any files you want the bot to share with users."
        )


def _generate_instruction_suggestions(max_instructions: int = 5):
    """Generate instruction suggestions based on current persona."""
    with st.spinner("Generating instruction suggestions..."):
        try:
            payload = {
                "custom_persona": st.session_state.custom_persona,
                "max_instructions": max_instructions,
            }

            resp = requests.post(
                GENERATE_INSTRUCTIONS_ENDPOINT,
                json=payload,
                timeout=API_GENERATE_TIMEOUT,
            )

            if resp.status_code != 200:
                st.error("Failed to generate instruction suggestions")
                return

            data = resp.json()
            # Extract instructions list from response
            instructions = data.get("instructions", {})
            if isinstance(instructions, dict):
                instruction_list = instructions.get("instructions", [])
            elif isinstance(instructions, list):
                instruction_list = instructions
            else:
                instruction_list = []

            if instruction_list:
                st.session_state._pd_instruction_suggestions = instruction_list
                st.success(
                    f"Generated {len(instruction_list)} instruction suggestions ✅"
                )
            else:
                st.warning("No instructions were generated. Try again.")

        except requests.exceptions.Timeout:
            st.error("Request timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error generating instructions: {e}")
            st.error(f"Error: {e}")


def _convert_assets_for_storage(editor_assets: list) -> list:
    """Convert assets from editor format to model/storage format."""
    result = []
    for a in editor_assets:
        if a.get("Name"):  # Only include assets with a name
            result.append({
                "asset_id": a.get("ID", ""),
                "asset_name": a.get("Name", ""),
                "asset_path": a.get("Path / URL", ""),
                "asset_description": a.get("Description", ""),
                "asset_type": a.get("Asset Type", ""),
                "other_info": a.get("Other Info", ""),
            })
    return result


def _commit_persona_silent():
    ss = st.session_state

    probing = [
        {
            "id": q["ID"],
            "question": q["Question"],
            "score": _clean_float(q["Score"]),
            "priority": int(q["Priority"]),
            "mandatory": bool(q["Mandatory"]),
        }
        for q in ss.get("_pd_questions_editor", [])
        if q.get("Question")
    ]

    # Parse products from data editor
    products_list = []
    edited_products = ss.get("_pd_products_data", [])
    for p in edited_products:
        if p.get("Name"):  # Only add if name exists
            products_list.append(
                {
                    "id": p.get("ID", f"prod_{len(products_list)+1:03d}"),
                    "name": p.get("Name", ""),
                    "description": p.get("Description", ""),
                    "base_pricing": _clean_float(p.get("Base Pricing"), default=None),
                    # Removing these as they are no longer in the editor
                    "currency": p.get("Currency") or ss.get("_pd_negotiation_config", {}).get("currency", "INR"),
                    "max_discount_percent": _clean_float(p.get("Max Discount %")), 
                    "discount_strategy": "",
                }
            )

    # Parse working hours from data editor
    working_hours_list = []
    edited_hours = ss.get("_pd_working_hours_data", [])
    for wh in edited_hours:
        if wh.get("Day"):
            working_hours_list.append(
                {
                    "day": wh.get("Day", ""),
                    "type": wh.get("Type", "Working"),
                    "start_time": wh.get("Start Time", "") or None,
                    "end_time": wh.get("End Time", "") or None,
                }
            )

    # Parse company management from data editor
    management_list = []
    edited_mgmt = ss.get("_pd_management_data", [])
    for m in edited_mgmt:
        if m.get("Name"):  # Only add if name exists
            management_list.append(
                {
                    "name": m.get("Name", ""),
                    "designation": m.get("Designation", ""),
                    "email": m.get("Email", ""),
                    "phone_number": m.get("Phone", ""),
                }
            )
            
    # Negotiation Config
    neg_config = ss.get("_pd_negotiation_config", {})
    negotiation_config = {
        "max_discount_percent": _clean_float(neg_config.get("max_discount_percent", 5.0), default=5.0),
        "currency": neg_config.get("currency", "INR"),
    }

    persona = {
        "name": ss.get("_pd_name", ""),
        "industry": ss.get("_pd_industry", ""),
        "category": ss.get("_pd_category", ""),
        "sub_category": ss.get("_pd_sub_category", ""),
        "business_type": ss.get("_pd_business_type", ""),
        "company_name": ss.get("_pd_company_name", ""),
        "company_domain": ss.get("_pd_company_domain", ""),
        "company_description": ss.get("_pd_company_desc", ""),
        "company_products": products_list,
        "negotiation_config": negotiation_config,
        "core_usps": ss.get("_pd_core_usps", ""),
        "core_features": ss.get("_pd_core_features", ""),
        "contact_info": ss.get("_pd_contact_info", ""),
        "offer_description": ss.get("_pd_offer_desc", ""),
        "prompt": ss.get("_pd_prompt", ""),
        "rules": ss.get("_pd_rules", "").splitlines(),
        "personality": ss.get("_pd_personality", ""),
        "business_focus": ss.get("_pd_business_focus", ""),
        "goal_type": ss.get("_pd_goal_type", ""),
        "language": ss.get("_pd_language", "en"),
        "use_emoji": ss.get("_pd_use_emoji", True),
        "use_name_reference": ss.get("_pd_use_name_reference", True),
        "enable_probing": ss.get("_pd_enable_probing", True),
        "probing_threshold": ss.get("_pd_probing_threshold", 50),
        "probing_questions": probing,
        "objection_count_limit": ss.get("_pd_objection_count", 3),
        "current_cta": ss.get("_pd_current_cta", ""),
        "working_hours": working_hours_list if working_hours_list else None,
        "company_management": management_list if management_list else None,
        "templates": ss.get("_pd_templates_data", []) or [],
        "assets": _convert_assets_for_storage(ss.get("_pd_assets_data", []) or []),
    }

    ss.custom_persona = persona

    if ss.get("auth_user_id"):
        save_user_persona(ss.auth_user_id, persona)
    else:
        save_global_persona(persona)


def _reset_persona():
    default = get_default_persona()
    st.session_state.custom_persona = default

    if st.session_state.get("auth_user_id"):
        save_user_persona(st.session_state.auth_user_id, default)
    else:
        save_global_persona(default)

    st.toast("Reset to default persona 🔄")


def _run_autofill(
    url: str, max_depth: int, max_pages: int, max_tokens: int, max_products: int
):
    """Call the autofill API and apply the response."""
    with st.spinner(
        "🌐 Crawling website and extracting persona... This may take a few minutes."
    ):
        try:
            # Get user_id from session state for KB ingestion
            user_id = st.session_state.get("auth_user_id", "")
            if not user_id:
                st.error("User ID not found. Please log in again.")
                return

            resp = requests.post(
                AUTOFILL_PERSONA_ENDPOINT,
                json={
                    "user_id": user_id,
                    "url": url,
                    "max_depth": max_depth,
                    "max_pages": max_pages,
                    "max_tokens": max_tokens,
                    "max_products": max_products,
                },
                timeout=API_AUTOFILL_TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                pages_analyzed = data.get("pages_analyzed", 0)
                bot_persona = data.get("bot_persona", {})

                if bot_persona:
                    _apply_autofill_response(bot_persona)
                    st.toast(
                        f"✅ Autofilled persona from {pages_analyzed} pages!", icon="🎉"
                    )

                    # Auto-generate templates after persona autofill
                    st.toast("📝 Generating templates...", icon="⏳")
                    _generate_templates_for_autofill(max_products)

                    st.toast("✅ Templates generated! Reloading UI...", icon="📝")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.warning("No persona data was extracted. Try a different URL.")
            else:
                st.error(f"Failed to autofill: {resp.status_code} - {resp.text}")
        except requests.exceptions.Timeout:
            st.error(
                "Request timed out. The website may be too large. Try reducing max pages."
            )
        except Exception as e:
            logger.error(f"Autofill error: {e}")
            st.error(f"Error: {e}")


def _apply_autofill_response(bot_persona: dict):
    """Apply the autofilled persona to session state and UI fields."""
    ss = st.session_state

    # Update the main persona store
    ss.custom_persona = bot_persona

    # Update all _pd_* session state variables for immediate UI refresh
    ss._pd_name = bot_persona.get("name", "")
    ss._pd_industry = bot_persona.get("industry", "")
    ss._pd_category = bot_persona.get("category", "")
    ss._pd_sub_category = bot_persona.get("sub_category", "")
    ss._pd_business_type = bot_persona.get("business_type", "")
    ss._pd_company_name = bot_persona.get("company_name", "")
    ss._pd_company_domain = bot_persona.get("company_domain", "")
    ss._pd_company_desc = bot_persona.get("company_description", "")
    ss._pd_contact_info = bot_persona.get("contact_info", "")
    ss._pd_personality = bot_persona.get("personality", "")
    ss._pd_business_focus = bot_persona.get("business_focus", "")
    ss._pd_goal_type = bot_persona.get("goal_type", "")
    ss._pd_language = bot_persona.get("language", "en")
    ss._pd_current_cta = bot_persona.get("current_cta", "")
    ss._pd_use_emoji = bot_persona.get("use_emoji", False)
    ss._pd_use_name_reference = bot_persona.get("use_name_reference", False)
    ss._pd_enable_probing = bot_persona.get("enable_probing", False)
    ss._pd_probing_threshold = bot_persona.get("probing_threshold", 50)
    ss._pd_objection_count = bot_persona.get("objection_count_limit", 3)
    ss._pd_prompt = bot_persona.get("prompt", "")
    ss._pd_rules = "\n".join(bot_persona.get("rules", []) or [])
    ss._pd_offer_desc = bot_persona.get("offer_description", "")
    ss._pd_core_usps = bot_persona.get("core_usps", "")
    ss._pd_core_features = bot_persona.get("core_features", "")
    
    # Negotiation Config
    neg_config = bot_persona.get("negotiation_config") or {}
    ss._pd_negotiation_config = {
        "currency": neg_config.get("currency", "INR"),
    }

    # Products
    products = bot_persona.get("company_products", []) or []
    ss._pd_products_data = (
        [
            {
                "ID": p.get("id", f"prod_{i+1:03d}"),
                "Name": p.get("name", ""),
                "Description": p.get("description", ""),
                "Base Pricing": p.get("base_pricing"),
                "Max Discount %": p.get("max_discount_percent", 0.0),
            }
            for i, p in enumerate(products)
        ]
        if products
        else []
    )

    # Working Hours
    working_hours = bot_persona.get("working_hours", []) or []
    default_working_hours = [
        {
            "Day": "Monday",
            "Type": "Working",
            "Start Time": "10:00",
            "End Time": "19:00",
        },
        {
            "Day": "Tuesday",
            "Type": "Working",
            "Start Time": "10:00",
            "End Time": "19:00",
        },
        {
            "Day": "Wednesday",
            "Type": "Working",
            "Start Time": "10:00",
            "End Time": "19:00",
        },
        {
            "Day": "Thursday",
            "Type": "Working",
            "Start Time": "10:00",
            "End Time": "19:00",
        },
        {
            "Day": "Friday",
            "Type": "Working",
            "Start Time": "10:00",
            "End Time": "19:00",
        },
        {"Day": "Saturday", "Type": "Holiday", "Start Time": "", "End Time": ""},
        {"Day": "Sunday", "Type": "Holiday", "Start Time": "", "End Time": ""},
    ]

    if working_hours:
        ss._pd_working_hours_data = [
            {
                "Day": wh.get("day", ""),
                "Type": wh.get("type", "Working"),
                "Start Time": wh.get("start_time", "") or "",
                "End Time": wh.get("end_time", "") or "",
            }
            for wh in working_hours
        ]
    else:
        ss._pd_working_hours_data = default_working_hours

    # Company Management
    management = bot_persona.get("company_management", []) or []
    if management:
        ss._pd_management_data = [
            {
                "Name": m.get("name", ""),
                "Designation": m.get("designation", ""),
                "Email": m.get("email", ""),
                "Phone": m.get("phone_number", ""),
            }
            for m in management
        ]
    else:
        ss._pd_management_data = [
            {"Name": "", "Designation": "", "Email": "", "Phone": ""}
        ]

    # Probing questions
    questions = bot_persona.get("probing_questions", []) or []
    ss._pd_questions_editor = (
        [
            {
                "ID": q.get("id", f"q_{i+1}"),
                "Question": q.get("question", ""),
                "Score": q.get("score", 10.0),
                "Priority": q.get("priority", i + 1),
                "Mandatory": q.get("mandatory", False),
            }
            for i, q in enumerate(questions)
        ]
        if questions
        else [
            {
                "ID": "q_1",
                "Question": "",
                "Score": 10.0,
                "Priority": 1,
                "Mandatory": False,
            }
        ]
    )

    # Templates
    templates = bot_persona.get("templates", []) or []
    ss._pd_templates_data = templates

    # Assets
    assets = bot_persona.get("assets", []) or []
    ss._pd_assets_data = (
        [
            {
                "ID": a.get("asset_id", ""),
                "Name": a.get("asset_name", ""),
                "Path / URL": a.get("asset_path", ""),
                "Description": a.get("asset_description", ""),
                "Asset Type": a.get("asset_type", ""),
                "Other Info": a.get("other_info", ""),
            }
            for a in assets
        ]
        if assets
        else []
    )

    # Save to database
    _commit_persona_silent()


def _generate_templates_for_autofill(max_products: int = 5):
    """Generate templates silently during autofill (no spinner since already in spinner)."""
    try:
        payload = {
            "custom_persona": st.session_state.custom_persona,
            "max_products": max_products,
        }

        resp = requests.post(
            GENERATE_TEMPLATES_ENDPOINT,
            json=payload,
            timeout=API_GENERATE_TIMEOUT,
        )

        if resp.status_code == 200:
            data = resp.json()
            templates = data.get("templates", [])
            if templates:
                st.session_state._pd_templates_data = templates
                _commit_persona_silent()
    except Exception as e:
        logger.error(f"Error generating templates during autofill: {e}")

