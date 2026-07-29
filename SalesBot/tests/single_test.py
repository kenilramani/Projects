"""Single test case for demo booking flow."""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import requests
import uuid

BASE_URL = "http://localhost:8000"


def create_test_payload(user_id: str, user_query: str, chat_history: list = None):
    """Create a test payload for the API."""
    return {
        "user_context": {
            "user_id": user_id,
            "user_query": user_query,
            "tenant_id": "test_tenant",
            "chat_history": chat_history or [],
            "timezone": "America/New_York",
            "region_code": "US",
            "collected_fields": {},
        },
        "bot_persona": {
            "name": "Arya",
            "industry": "Technology",
            "category": "SaaS",
            "sub_category": "AI Solutions",
            "business_type": "B2B",
            "company_name": "AI Sante",
            "company_domain": "aisante.com",
            "company_description": "AI Sante provides AI-powered sales and support solutions.",
            "company_products": [
                {
                    "id": "prod_001",
                    "name": "AI Sales Bot",
                    "description": "Intelligent sales assistant",
                },
                {
                    "id": "prod_002",
                    "name": "Support Copilot",
                    "description": "AI-powered support",
                },
            ],
            "core_usps": "24/7 availability, intelligent lead qualification",
            "core_features": "Lead scoring, automated follow-ups, demo scheduling",
            "contact_info": "sales@aisante.com",
            "language": "English",
            "rules": ["Be professional", "Guide towards booking a demo"],
            "offer_description": "Free 14-day trial",
            "prompt": "",
            "personality": "Friendly and professional",
            "business_focus": "Enterprise sales automation",
            "goal_type": "demo_booking",
            "use_emoji": False,
            "use_name_reference": True,
            "probing_questions": [],
            "probing_threshold": 50,
            "enable_probing": True,
            "current_cta": "Book a Demo",
            "objection_count_limit": 3,
        },
    }


def test_demo_booking_flow():
    """Test a demo booking conversation flow."""
    user_id = str(uuid.uuid4())
    print(f"\n{'='*60}")
    print("TEST: Demo Booking Flow")
    print(f"User ID: {user_id}")
    print("=" * 60)

    messages = [
        "Hi, I'd like to book a demo",
        "Tomorrow at 3pm works for me",
        "My email is john@example.com",
    ]

    chat_history = []

    for i, msg in enumerate(messages, 1):
        print(f"\n--- Message {i}: {msg} ---")
        try:
            payload = create_test_payload(user_id, msg, chat_history)
            response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=120)

            if response.status_code == 200:
                data = response.json()
                # Debug: print full response keys
                print(f"Response keys: {list(data.keys())}")
                reply = (
                    data.get("reply")
                    or data.get("response")
                    or data.get("message")
                    or str(data)[:300]
                )
                agent = (
                    data.get("agent")
                    or data.get("agent_name")
                    or data.get("last_agent")
                    or "Unknown"
                )
                print(f"Agent: {agent}")
                print(
                    f"Reply: {reply[:200]}..."
                    if len(str(reply)) > 200
                    else f"Reply: {reply}"
                )
                print("Status: SUCCESS")

                # Add to chat history for next message
                chat_history.append({"role": "user", "content": msg})
                chat_history.append({"role": "assistant", "content": reply})
            else:
                print(f"Status: FAILED (HTTP {response.status_code})")
                print(f"Error: {response.text[:300]}")
        except Exception as e:
            print(f"Status: ERROR - {str(e)}")

    print(f"\n{'='*60}")
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    test_demo_booking_flow()
