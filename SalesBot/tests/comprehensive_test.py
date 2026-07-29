"""
Comprehensive API Test Script - For detailed testing of the BotRunner API.

Tests various scenarios with detailed output including errors.
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
    print("\n" + "=" * 100)
    print(f"🧪 TEST: {test_name}")
    print(f"❓ QUERY: {query}")
    print("-" * 100)

    if result.get("status_code") == 200:
        response_data = result.get("response", {})
        bot_response = response_data.get("response", "No response")
        print(f"✅ STATUS: SUCCESS (200)")
        print(f"🤖 BOT RESPONSE:\n{bot_response}")

        # Show additional details if present
        if response_data.get("last_agent"):
            print(f"🎯 LAST AGENT: {response_data.get('last_agent')}")
        if response_data.get("user_id"):
            print(f"👤 USER ID: {response_data.get('user_id')}")
        if response_data.get("probing_score"):
            print(f"📊 PROBING SCORE: {response_data.get('probing_score')}")
        if response_data.get("collected_fields"):
            print(
                f"📝 COLLECTED FIELDS: {json.dumps(response_data.get('collected_fields'), indent=2)}"
            )

        # Check if error response
        is_error = "I apologize, but I encountered an issue" in bot_response
        if is_error:
            print("⚠️ WARNING: Response indicates an error occurred on the server side!")
            return False
        return True
    else:
        print(f"❌ STATUS: FAILED ({result.get('status_code')})")
        print(
            f"💥 ERROR: {result.get('response', result.get('error', 'Unknown error'))}"
        )
        return False

    print("=" * 100)


def test_scenario(name: str, user_id: str, queries: list, delay: float = 2.0):
    """Test a multi-turn conversation scenario."""
    print(f"\n\n{'#' * 100}")
    print(f"🎬 SCENARIO: {name}")
    print(f"👤 USER ID: {user_id}")
    print(f"{'#' * 100}")

    chat_history = []
    results = []

    for i, query in enumerate(queries):
        print(f"\n--- Turn {i+1}/{len(queries)} ---")
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

        time.sleep(delay)

    passed_count = sum(results)
    print(f"\n📊 Scenario '{name}' Results: {passed_count}/{len(results)} passed")
    return all(results)


def main():
    """Run comprehensive API tests."""
    print("\n" + "🚀" * 50)
    print("COMPREHENSIVE BOTRUNNER API TEST SUITE")
    print("🚀" * 50)

    all_results = []

    # Wait for server to be ready
    print("\n⏳ Waiting for server to be ready...")
    time.sleep(3)

    # ==========================================
    # SCENARIO 1: New User - Basic Sales Flow
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
    # SCENARIO 2: Demo Booking Complete Flow
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
    # SCENARIO 3: Human Escalation Flow
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
    # SCENARIO 4: Product Inquiry Flow
    # ==========================================
    user_4 = str(uuid.uuid4())
    queries_4 = [
        "What does your Support Copilot do?",
        "How does it integrate with existing systems?",
        "What about security?",
        "Sounds good, how do I get started?",
    ]
    all_results.append(test_scenario("Product Inquiry Flow", user_4, queries_4))

    # ==========================================
    # SCENARIO 5: Objection Handling Flow
    # ==========================================
    user_5 = str(uuid.uuid4())
    queries_5 = [
        "Tell me about your AI Sales Bot",
        "It seems expensive",
        "We tried AI tools before and they didn't work well",
        "How is your product different?",
        "Ok, I'll consider it",
    ]
    all_results.append(test_scenario("Objection Handling Flow", user_5, queries_5))

    # ==========================================
    # SCENARIO 6: Same User Multiple Sessions
    # ==========================================
    persistent_user = str(uuid.uuid4())

    # First session
    print(f"\n\n{'='*100}")
    print("🔄 MULTI-SESSION TEST - Session 1")
    print(f"{'='*100}")

    session1_queries = [
        "Hi, I'm Mike from RetailCo",
        "We're looking for sales automation",
    ]
    all_results.append(
        test_scenario("Persistent User - Session 1", persistent_user, session1_queries)
    )

    # Second session (same user)
    print(f"\n\n{'='*100}")
    print("🔄 MULTI-SESSION TEST - Session 2 (Same User)")
    print(f"{'='*100}")

    session2_queries = [
        "Hi again, I want to continue our conversation",
        "Can you tell me more about pricing?",
    ]
    all_results.append(
        test_scenario("Persistent User - Session 2", persistent_user, session2_queries)
    )

    # ==========================================
    # SCENARIO 7: Edge Cases
    # ==========================================
    user_7 = str(uuid.uuid4())
    edge_cases = [
        "yes",
        "no",
        "maybe",
        "???",
        "I don't understand what you're saying",
    ]
    all_results.append(test_scenario("Edge Cases", user_7, edge_cases))

    # ==========================================
    # SCENARIO 8: Mixed Intent Flow
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
    print("\n\n" + "🎯" * 50)
    print("FINAL TEST SUMMARY")
    print("🎯" * 50)

    total_scenarios = len(all_results)
    passed_scenarios = sum(all_results)

    print(f"\n📊 Total Scenarios: {total_scenarios}")
    print(f"✅ Passed: {passed_scenarios}")
    print(f"❌ Failed: {total_scenarios - passed_scenarios}")
    print(f"📈 Success Rate: {passed_scenarios / total_scenarios * 100:.1f}%")

    return all_results


if __name__ == "__main__":
    main()
