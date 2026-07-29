"""
API Test Script - Comprehensive testing for the BotRunner API.

Tests various scenarios:
1. Initial greeting/first contact
2. Follow-up conversation  
3. Product inquiries
4. Booking requests
5. Human escalation
6. Different user IDs
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


def send_chat_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send a chat request and return the response."""
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60,
        )
        return {
            "status_code": response.status_code,
            "response": (
                response.json() if response.status_code == 200 else response.text
            ),
        }
    except requests.exceptions.RequestException as e:
        return {"status_code": 0, "error": str(e)}


def print_result(test_name: str, query: str, result: Dict[str, Any]):
    """Pretty print test results."""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print(f"QUERY: {query}")
    print("-" * 80)

    if result.get("status_code") == 200:
        response_data = result.get("response", {})
        bot_response = response_data.get("response", "No response")
        print(f"STATUS: ✅ SUCCESS (200)")
        print(f"BOT RESPONSE: {bot_response[:500]}...")

        # Show additional details if present
        if response_data.get("last_agent"):
            print(f"LAST AGENT: {response_data.get('last_agent')}")
    else:
        print(f"STATUS: ❌ FAILED ({result.get('status_code')})")
        print(
            f"ERROR: {result.get('response', result.get('error', 'Unknown error'))[:500]}"
        )

    print("=" * 80)
    return result.get("status_code") == 200


def run_conversation_test(user_id: str, messages: list, test_name: str) -> bool:
    """Run a multi-turn conversation test."""
    print(f"\n{'#' * 80}")
    print(f"CONVERSATION TEST: {test_name}")
    print(f"USER ID: {user_id}")
    print(f"{'#' * 80}")

    chat_history = []
    all_passed = True

    for i, msg in enumerate(messages):
        print(f"\n--- Turn {i+1} ---")
        payload = create_test_payload(
            user_id=user_id, user_query=msg, chat_history=chat_history
        )

        result = send_chat_request(payload)
        passed = print_result(f"Turn {i+1}", msg, result)
        all_passed = all_passed and passed

        if result.get("status_code") == 200:
            response_data = result.get("response", {})
            # Add to chat history for next turn
            chat_history.append({"role": "user", "content": msg})
            chat_history.append(
                {"role": "assistant", "content": response_data.get("response", "")}
            )

        # Small delay between turns
        time.sleep(1)

    return all_passed


def main():
    """Run all API tests."""
    print("\n" + "🚀" * 40)
    print("BOTRUNNER API TEST SUITE")
    print("🚀" * 40)

    results = {"passed": 0, "failed": 0, "tests": []}

    # Wait for server to be ready
    print("\nWaiting for server to be ready...")
    time.sleep(3)

    # Test 1: Basic greeting - new user
    print("\n\n" + "=" * 80)
    print("TEST SUITE 1: BASIC GREETINGS")
    print("=" * 80)

    user_id_1 = str(uuid.uuid4())
    test_queries_1 = [
        ("Initial Hello", "Hello, I'm interested in your AI solutions"),
        ("Affirmative Response", "Yes, tell me more about it"),
        ("Product Question", "What features does your AI Sales Bot have?"),
    ]

    for test_name, query in test_queries_1:
        payload = create_test_payload(user_id=user_id_1, user_query=query)
        result = send_chat_request(payload)
        passed = print_result(test_name, query, result)
        results["tests"].append({"name": test_name, "passed": passed})
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
        time.sleep(2)

    # Test 2: Multi-turn conversation - lead qualification
    print("\n\n" + "=" * 80)
    print("TEST SUITE 2: LEAD QUALIFICATION CONVERSATION")
    print("=" * 80)

    user_id_2 = str(uuid.uuid4())
    conversation_2 = [
        "Hi, I'm looking for a sales automation tool",
        "We have about 15 sales reps on our team",
        "We use Salesforce for CRM",
        "Our main challenge is qualifying leads quickly",
    ]

    passed = run_conversation_test(user_id_2, conversation_2, "Lead Qualification Flow")
    results["tests"].append(
        {"name": "Lead Qualification Conversation", "passed": passed}
    )
    if passed:
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 3: Booking request scenario
    print("\n\n" + "=" * 80)
    print("TEST SUITE 3: DEMO BOOKING SCENARIO")
    print("=" * 80)

    user_id_3 = str(uuid.uuid4())
    conversation_3 = [
        "I'd like to see a demo of your product",
        "I'm available tomorrow at 2pm",
        "My email is test@example.com",
    ]

    passed = run_conversation_test(user_id_3, conversation_3, "Demo Booking Flow")
    results["tests"].append({"name": "Demo Booking Conversation", "passed": passed})
    if passed:
        results["passed"] += 1
    else:
        results["failed"] += 1

    # Test 4: Human escalation scenario
    print("\n\n" + "=" * 80)
    print("TEST SUITE 4: HUMAN ESCALATION")
    print("=" * 80)

    user_id_4 = str(uuid.uuid4())
    test_queries_4 = [
        ("Request Human", "I want to talk to a human representative"),
        (
            "Complaint",
            "I'm frustrated with the automated responses, please connect me to someone",
        ),
    ]

    for test_name, query in test_queries_4:
        payload = create_test_payload(user_id=user_id_4, user_query=query)
        result = send_chat_request(payload)
        passed = print_result(test_name, query, result)
        results["tests"].append({"name": test_name, "passed": passed})
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
        time.sleep(2)

    # Test 5: Edge cases
    print("\n\n" + "=" * 80)
    print("TEST SUITE 5: EDGE CASES")
    print("=" * 80)

    user_id_5 = str(uuid.uuid4())
    edge_cases = [
        ("Short Response", "yes"),
        ("Question", "How does your pricing work?"),
        ("Objection", "I think it's too expensive for us"),
        ("Off-topic", "What's the weather like today?"),
    ]

    for test_name, query in edge_cases:
        payload = create_test_payload(user_id=user_id_5, user_query=query)
        result = send_chat_request(payload)
        passed = print_result(test_name, query, result)
        results["tests"].append({"name": test_name, "passed": passed})
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
        time.sleep(2)

    # Test 6: Same user multiple sessions
    print("\n\n" + "=" * 80)
    print("TEST SUITE 6: PERSISTENT USER SESSION")
    print("=" * 80)

    persistent_user = "a380a64b-a77f-4674-ab38-6a0e93d253b7"  # Original test user ID
    persistent_queries = [
        ("First Contact", "Hello, I'm John from TechCorp"),
        ("Follow-up", "Tell me about your AI Sales Bot"),
        ("Interest", "That sounds interesting, how do I get started?"),
    ]

    for test_name, query in persistent_queries:
        payload = create_test_payload(user_id=persistent_user, user_query=query)
        result = send_chat_request(payload)
        passed = print_result(test_name, query, result)
        results["tests"].append(
            {"name": f"Persistent User - {test_name}", "passed": passed}
        )
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
        time.sleep(2)

    # Print final summary
    print("\n\n" + "🎯" * 40)
    print("TEST RESULTS SUMMARY")
    print("🎯" * 40)
    print(f"\nTotal Tests: {results['passed'] + results['failed']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(
        f"Success Rate: {results['passed'] / (results['passed'] + results['failed']) * 100:.1f}%"
    )

    print("\nDetailed Results:")
    for test in results["tests"]:
        status = "✅" if test["passed"] else "❌"
        print(f"  {status} {test['name']}")

    return results


if __name__ == "__main__":
    main()
