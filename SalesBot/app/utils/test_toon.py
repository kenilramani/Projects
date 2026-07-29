from toon import encode
import json

data = {
    "user_context": {
        "user_id": "a2e2d660-a10f-4e23-8482-f7cff8271091",
        "tenant_id": "42dd666a-67f7-4b11-bd9b-ae5170c8d5d7",
        "user_query": "full body checkup",
        "chat_summary": "",
        "executive_summary": "",
        "chat_history": [
            {
                "role": "user",
                "content": "hiii"
            },
            {
                "role": "assistant",
                "content": "Hello! Welcome to APEX DIABETES - THYROID SUPERSPECIALTY HORMONE CLINIC. How can I assist you today?"
            },
            {
                "role": "user",
                "content": "may i know your products?"
            },
            {
                "role": "assistant",
                "content": "We provide Diabetes Care, Thyroid Care, PCOS / PCOD Treatment, Obesity Care, and Full Body Checkup."
            },
            {
                "role": "user",
                "content": "for myself"
            },
            {
                "role": "assistant",
                "content": "Which health concern would you like help with?"
            },
            {
                "role": "user",
                "content": "full body checkup"
            }
        ],
        "to_summarise": False,
        "retrieved_docs": [],
        "contact_details": None,
        "lead_details": None,
        "follow_trigger": False,
        "ask_new_date": False,
        "previous_time": None,
        "previous_date": None,
        "timezone": None,
        "region_code": None,
        "ismultiple_timezone": False,
        "collected_fields": None,
        "all_info_collected": False,
        "booking_confirmed": False,
        "booking_type": None,
        "new_booking": True,
        "cache_pairs": None,
        "last_agent": "sales_agent"
    },
    "bot_persona": {
        "name": "Apex Diabetes Agent",
        "industry": "Healthcare",
        "category": "Medical Clinic",
        "sub_category": "Diabetes & Thyroid Superspecialty",
        "business_type": "B2C",
        "company_name": "APEX DIABETES - THYROID SUPERSPECIALTY HORMONE CLINIC",
        "company_domain": "apexdiabetesthyroid.com",
        "company_description": "Superspecialty hormone clinic in Rajkot focused on diabetes, thyroid, PCOS, obesity and metabolic health.",
        "goal_type": "appointment_booking",
        "use_emoji": False,
        "use_name_reference": False,
        "enable_probing": True,
        "probing_threshold": 40,
        "current_cta": "Book an Appointment"
    },
    "response": "Great! Full Body Checkup is a very good choice. Are you looking for a routine preventive checkup or do you have any specific symptoms?",
    "probing_context": {
        "detected_question_answer": [],
        "total_score": 0,
        "probing_completed": False,
        "can_show_cta": False,
        "is_objection": False
    },
    "objection_state": {
        "current_objection_count": 0,
        "is_objection_limit_reached": False
    }
}

# Ensure fully serializable JSON before encoding
data = json.loads(json.dumps(data))

toon_data = encode(data)

print(type(toon_data))