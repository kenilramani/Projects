"""
Agent Flow Test Script - Selected 20 query limit.
"""

import requests
import json
import time
import uuid
import sys
import io
from typing import Dict, Any, Optional

# Fix Windows encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

API_LOG_FILE = "test_results.log"


def log_output(message: str):
    """Log output to both stdout and file."""
    print(message)
    with open(API_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")


BASE_URL = "http://127.0.0.1:8000"


def create_test_payload(
    user_id: str,
    user_query: str,
    chat_history: list = None,
    company_name: str = "AI Sante",
    bot_name: str = "Arya",
    enable_probing: bool = True,
) -> Dict[str, Any]:
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
            "name": bot_name,
            "industry": "Technology",
            "category": "SaaS",
            "sub_category": "AI Solutions",
            "business_type": "B2B",
            "company_name": company_name,
            "company_domain": "aisante.com",
            "company_description": "AI Sante provides AI-powered sales and support solutions for B2B companies.",
            "company_products": [
                {
                    "id": "prod_001",
                    "name": "AI Sales Bot",
                    "description": "Intelligent sales assistant that qualifies leads and books demos",
                },
                {
                    "id": "prod_002",
                    "name": "Support Copilot",
                    "description": "AI-powered customer support automation",
                },
            ],
            "core_usps": "24/7 availability, intelligent lead qualification, seamless CRM integration",
            "core_features": "Lead scoring, automated follow-ups, demo scheduling, analytics dashboard",
            "contact_info": "sales@aisante.com",
            "language": "English",
            "rules": [
                "Always be professional and helpful",
                "Focus on understanding customer needs",
                "Guide towards booking a demo when appropriate",
            ],
            "offer_description": "Free 14-day trial with full feature access",
            "prompt": "",
            "personality": "Friendly, professional, and knowledgeable",
            "business_focus": "Enterprise sales automation",
            "goal_type": "demo_booking",
            "use_emoji": False,
            "use_name_reference": True,
            "probing_questions": [
                {
                    "id": "q1",
                    "question": "What's the size of your sales team?",
                    "score": 20,
                    "priority": 1,
                    "mandatory": True,
                },
                {
                    "id": "q2",
                    "question": "What CRM are you currently using?",
                    "score": 15,
                    "priority": 2,
                    "mandatory": False,
                },
                {
                    "id": "q3",
                    "question": "What are your main challenges with lead qualification?",
                    "score": 25,
                    "priority": 1,
                    "mandatory": True,
                },
            ],
            "probing_threshold": 50,
            "enable_probing": enable_probing,
            "current_cta": "Book a demo",
            "objection_count_limit": 3,
        },
    }


def send_chat_request(payload: Dict[str, Any], verbose: bool = True) -> Dict[str, Any]:
    """Send a chat request and return the response."""
    try:
        if verbose:
            print(f"\n📤 Sending request...")
        response = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120,  # Increased timeout
        )
        result = {
            "status_code": response.status_code,
            "response": (
                response.json() if response.status_code == 200 else response.text
            ),
        }
        if verbose:
            print(f"📥 Received response (status: {response.status_code})")
        return result
    except requests.exceptions.RequestException as e:
        return {"status_code": 0, "error": str(e)}


def print_detailed_result(test_name: str, query: str, result: Dict[str, Any]):
    """Pretty print test results with full details."""
    log_output("\n" + "=" * 100)
    log_output(f"🧪 TEST: {test_name}")
    log_output(f"❓ QUERY: {query}")
    log_output("-" * 100)

    if result.get("status_code") == 200:
        response_data = result.get("response", {})
        bot_response = response_data.get("response", "No response")
        log_output(f"✅ STATUS: SUCCESS (200)")
        log_output(f"🤖 BOT RESPONSE:\n{bot_response}")

        # Show additional details if present
        if response_data.get("last_agent"):
            log_output(f"🎯 LAST AGENT: {response_data.get('last_agent')}")
        if response_data.get("user_id"):
            log_output(f"👤 USER ID: {response_data.get('user_id')}")
        if response_data.get("probing_score"):
            log_output(f"📊 PROBING SCORE: {response_data.get('probing_score')}")
        if response_data.get("collected_fields"):
            log_output(
                f"📝 COLLECTED FIELDS: {json.dumps(response_data.get('collected_fields'), indent=2)}"
            )

        # Check if error response
        is_error = "I apologize, but I encountered an issue" in bot_response
        if is_error:
            log_output(
                "⚠️ WARNING: Response indicates an error occurred on the server side!"
            )
            return False
        return True
    else:
        log_output(f"❌ STATUS: FAILED ({result.get('status_code')})")
        log_output(
            f"💥 ERROR: {result.get('response', result.get('error', 'Unknown error'))}"
        )
        return False

    log_output("=" * 100)


def test_scenario(name: str, user_id: str, queries: list, delay: float = 2.0):
    """Test a multi-turn conversation scenario."""
    log_output(f"\n\n{'#' * 100}")
    log_output(f"🎬 SCENARIO: {name}")
    log_output(f"👤 USER ID: {user_id}")
    log_output(f"{'#' * 100}")

    chat_history = []
    results = []

    for i, query in enumerate(queries):
        log_output(f"\n--- Turn {i+1}/{len(queries)} ---")
        payload = create_test_payload(
            user_id=user_id, user_query=query, chat_history=chat_history
        )

        result = send_chat_request(payload)
        passed = print_detailed_result(f"Turn {i+1}", query, result)
        results.append(passed)

        if result.get("status_code") == 200:
            response_data = result.get("response", {})
            # Add to chat history for next turn
            chat_history.append({"role": "user", "content": query})
            chat_history.append(
                {"role": "assistant", "content": response_data.get("response", "")}
            )

        # Be nice to the server
        time.sleep(delay)

    passed_count = sum(results)
    log_output(f"\n📊 Scenario '{name}' Results: {passed_count}/{len(results)} passed")
    return all(results)


def main():
    """Run selected API tests (Max 20 turns)."""
    # Clear log file
    with open(API_LOG_FILE, "w", encoding="utf-8") as f:
        f.write("")

    log_output("\n" + "🚀" * 50)
    log_output("AGENT FLOW TEST SUITE (MAX 20 TURNS)")
    log_output("🚀" * 50)

    all_results = []

    # Wait for server to be ready
    log_output("\n⏳ Waiting for server to be ready...")
    time.sleep(5)  # Giving it a bit more time as it's a separate process

    # Check if server is up
    try:
        requests.get(f"{BASE_URL}/docs", timeout=5)
    except Exception:
        log_output("⚠️ Server might not be ready. Waiting 5 more seconds...")
        time.sleep(5)

    # ==========================================
    # SCENARIO 1: New User - Basic Sales Flow (5 turns)
    # ==========================================
    user_1 = str(uuid.uuid4())
    queries_1 = [
        "Hi, I'm interested in learning about your products",
        "We're in the healthcare industry",
        "We have about 50 employees",
        "Our biggest challenge is lead management",
        "Can you tell me about your pricing?",
    ]
    all_results.append(test_scenario("New User - Basic Sales Flow", user_1, queries_1))

    # ==========================================
    # SCENARIO 2: Demo Booking Complete Flow (5 turns)
    # ==========================================
    user_2 = str(uuid.uuid4())
    queries_2 = [
        "I want to schedule a demo",
        "I'm interested in the AI Sales Bot",
        "My email is john@techcorp.com",
        "My name is John Smith",
        "Tomorrow at 3pm works for me",
    ]
    all_results.append(test_scenario("Demo Booking Complete Flow", user_2, queries_2))

    # ==========================================
    # SCENARIO 3: Human Escalation Flow (4 turns)
    # ==========================================
    user_3 = str(uuid.uuid4())
    queries_3 = [
        "Hello, I need help",
        "I want to speak with a real person",
        "My name is Sarah and my email is sarah@company.com",
        "I have questions about enterprise pricing",
    ]
    all_results.append(test_scenario("Human Escalation Flow", user_3, queries_3))

    # ==========================================
    # SCENARIO 4: Mixed Intent Flow (5 turns)
    # ==========================================
    user_8 = str(uuid.uuid4())
    mixed_queries = [
        "Hi, I have a question about your product",
        "Actually, can I book a demo?",
        "Wait, first tell me about pricing",
        "Ok now let's book that demo",
        "My email is test@example.com",
    ]
    all_results.append(test_scenario("Mixed Intent Flow", user_8, mixed_queries))

    # ==========================================
    # FINAL SUMMARY
    # ==========================================
    log_output("\n\n" + "🎯" * 50)
    log_output("FINAL TEST SUMMARY")
    log_output("🎯" * 50)

    total_scenarios = len(all_results)
    passed_scenarios = sum(all_results)

    log_output(f"\n📊 Total Scenarios: {total_scenarios}")
    log_output(f"✅ Passed: {passed_scenarios}")
    log_output(f"❌ Failed: {total_scenarios - passed_scenarios}")
    if total_scenarios > 0:
        log_output(f"📈 Success Rate: {passed_scenarios / total_scenarios * 100:.1f}%")
    else:
        log_output(f"📈 Success Rate: 0.0%")

    return all_results


if __name__ == "__main__":
    main()
