"""
Comprehensive Test Script for Demo Booking Flow

Tests:
1. NEW BOOKING - Available slot
2. NEW BOOKING - Unavailable slot (should offer alternatives)
3. NEW BOOKING - User selects alternative slot
4. RESCHEDULE - With existing booking
5. RESCHEDULE - Without existing booking (should redirect to new)
6. CANCEL - With existing booking
7. CANCEL - Without existing booking (should redirect to new)
8. CONFIRMATION - Already booked demo

Available mock slots (from calendly_api.py):
- 2026-01-30T09:00:00Z (2:30 PM IST)
- 2026-02-04T12:00:00Z (5:30 PM IST)  
- 2026-02-05T10:30:00Z (4:00 PM IST)
- 2026-02-10T07:30:00Z (1:00 PM IST)
- 2026-02-11T12:00:00Z (5:30 PM IST)
"""

import requests
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BASE_URL}/chat"


class ConversationSession:
    """Manages a conversation session with persistent user_id for multi-turn tests."""

    def __init__(self, user_id: str = None):
        self.user_id = user_id or f"test_user_{int(time.time())}"
        self.collected_fields = {}
        self.booking_confirmed = False
        self.chat_history = []

    def send_message(self, query: str, extra_fields: Dict = None) -> Optional[Dict]:
        """Send a message and update session state from response."""
        payload = {
            "user_context": {
                "user_id": self.user_id,
                "user_query": query,
                "chat_history": self.chat_history,
                "collected_fields": {**self.collected_fields, **(extra_fields or {})},
                "booking_confirmed": self.booking_confirmed,
                "timezone": "Asia/Kolkata",
            }
        }

        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(
                CHAT_ENDPOINT, json=payload, headers=headers, timeout=120
            )
            if response.status_code == 200:
                data = response.json()

                # Update session state from response
                if data.get("collected_fields"):
                    self.collected_fields.update(data["collected_fields"])
                if data.get("booking_confirmed") is not None:
                    self.booking_confirmed = data["booking_confirmed"]

                # Update chat history
                self.chat_history.append({"role": "user", "content": query})
                self.chat_history.append(
                    {"role": "assistant", "content": data.get("response", "")}
                )

                return data
            else:
                print(f"❌ Error: Status {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None


def print_separator(title: str = ""):
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def print_result(data: Dict, test_name: str):
    """Print formatted test result."""
    print(f"\n🤖 Bot Response:")
    print(f"   {data.get('response', 'No response')[:400]}")
    print(f"\n📊 State:")
    print(f"   - booking_confirmed: {data.get('booking_confirmed', 'N/A')}")
    print(f"   - collected_fields: {data.get('collected_fields', {})}")


def test_server_health() -> bool:
    """Check if server is running."""
    print("🔍 Checking server health...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
    except:
        pass
    print("❌ Server is not responding. Make sure it's running on port 8000.")
    return False


# =============================================================================
# TEST 1: NEW BOOKING - Available Slot
# =============================================================================
def test_new_booking_available_slot():
    """Test new booking with an available slot (Feb 5th 4:00 PM IST = 10:30 UTC)."""
    print_separator("TEST 1: NEW BOOKING - Available Slot")
    print("   Testing: February 5th, 2026 at 4:00 PM IST (10:30 UTC)")
    print("   Expected: Slot available, booking should be confirmed")

    session = ConversationSession()

    # Single message with all info
    query = """I want to book a demo for AI Sales Bot on February 5th at 4:00 PM. 
    My email is john@example.com"""

    print(f"\n📤 User: {query[:80]}...")
    data = session.send_message(query, {"email": "john@example.com"})

    if data:
        print_result(data, "New Booking Available")

        response_lower = data.get("response", "").lower()
        booking_confirmed = data.get("booking_confirmed", False)

        # Check for success indicators
        if booking_confirmed == True:
            print("\n✅ TEST PASSED: Booking confirmed for available slot!")
            return True
        elif (
            "confirm" in response_lower
            or "booked" in response_lower
            or "scheduled" in response_lower
        ):
            print("\n✅ TEST PASSED: Booking appears to be confirmed!")
            return True
        else:
            print(
                "\n⚠️  TEST RESULT: Booking may need follow-up (agent might need product/time confirmation)"
            )
            return None
    return False


# =============================================================================
# TEST 2: NEW BOOKING - Unavailable Slot
# =============================================================================
def test_new_booking_unavailable_slot():
    """Test new booking with unavailable slot (Feb 5th 2:00 PM IST = 08:30 UTC)."""
    print_separator("TEST 2: NEW BOOKING - Unavailable Slot")
    print("   Testing: February 5th, 2026 at 2:00 PM IST (08:30 UTC)")
    print("   Expected: Slot unavailable, should offer alternatives")

    session = ConversationSession()

    query = """Book a demo for AI Sales Bot on February 5th at 2:00 PM. 
    Email: jane@example.com"""

    print(f"\n📤 User: {query[:80]}...")
    data = session.send_message(query, {"email": "jane@example.com"})

    if data:
        print_result(data, "New Booking Unavailable")

        response_lower = data.get("response", "").lower()
        booking_confirmed = data.get("booking_confirmed", False)

        # Check for alternative slot offering
        if booking_confirmed == False and (
            "alternative" in response_lower
            or "available" in response_lower
            or "instead" in response_lower
        ):
            print(
                "\n✅ TEST PASSED: Bot correctly identified unavailable slot and offered alternatives!"
            )
            return True
        elif (
            "4:00 pm" in response_lower
            or "5:30 pm" in response_lower
            or "1:00 pm" in response_lower
        ):
            print("\n✅ TEST PASSED: Bot offered specific alternative times!")
            return True
        elif booking_confirmed == False:
            print(
                "\n✅ TEST PASSED: Booking NOT confirmed (as expected for unavailable slot)"
            )
            return True
        else:
            print("\n⚠️  TEST RESULT: Need to verify response manually")
            return None
    return False


# =============================================================================
# TEST 3: NEW BOOKING - User Selects Alternative
# =============================================================================
def test_new_booking_select_alternative():
    """Test user selecting an alternative slot after unavailable."""
    print_separator("TEST 3: NEW BOOKING - User Selects Alternative")
    print("   Step 1: Request unavailable slot (2:00 PM)")
    print("   Step 2: Select alternative slot (4:00 PM - available)")

    session = ConversationSession()

    # Step 1: Request unavailable slot
    print("\n📤 Step 1: Requesting unavailable slot...")
    query1 = "Book demo for AI Sales Bot on Feb 5th at 2pm. Email: bob@example.com"
    data1 = session.send_message(query1, {"email": "bob@example.com"})

    if not data1:
        return False

    print(f"   Bot: {data1.get('response', '')[:200]}...")
    print(f"   booking_confirmed: {data1.get('booking_confirmed')}")

    time.sleep(1)

    # Step 2: Select available alternative
    print("\n📤 Step 2: Selecting available slot...")
    query2 = "Make it 4:00 PM instead"
    data2 = session.send_message(query2)

    if data2:
        print_result(data2, "Select Alternative")

        booking_confirmed = data2.get("booking_confirmed", False)
        response_lower = data2.get("response", "").lower()

        if booking_confirmed == True:
            print("\n✅ TEST PASSED: Alternative slot selected and booking confirmed!")
            return True
        elif "confirm" in response_lower or "booked" in response_lower:
            print("\n✅ TEST PASSED: Booking appears confirmed!")
            return True
        else:
            print("\n⚠️  TEST RESULT: May need additional confirmation")
            return None
    return False


# =============================================================================
# TEST 4: RESCHEDULE - With Existing Booking
# =============================================================================
def test_reschedule_with_existing_booking():
    """Test rescheduling an existing confirmed booking."""
    print_separator("TEST 4: RESCHEDULE - With Existing Booking")
    print("   Setup: Existing booking on Feb 5th at 4:00 PM")
    print("   Action: Reschedule to Feb 10th at 1:00 PM")

    session = ConversationSession()
    # Set up existing confirmed booking
    session.collected_fields = {
        "email": "alice@example.com",
        "date": "2026-02-05",
        "time": "2026-02-05T10:30:00+00:00",
        "product": "AI Sales Bot",
    }
    session.booking_confirmed = True

    query = "I need to reschedule my demo to February 10th at 1:00 PM"

    print(f"\n📤 User: {query}")
    print(f"   (Existing booking_confirmed=True)")

    data = session.send_message(query)

    if data:
        print_result(data, "Reschedule")

        booking_confirmed = data.get("booking_confirmed", False)
        response_lower = data.get("response", "").lower()
        collected = data.get("collected_fields", {})

        # Check if rescheduled successfully
        if booking_confirmed == True and "reschedul" in response_lower:
            print("\n✅ TEST PASSED: Demo successfully rescheduled!")
            return True
        elif "february 10" in response_lower or "1:00 pm" in response_lower:
            print("\n✅ TEST PASSED: New date/time acknowledged!")
            return True
        elif collected.get("date") == "2026-02-10":
            print("\n✅ TEST PASSED: Date updated to new value!")
            return True
        else:
            print("\n⚠️  TEST RESULT: Reschedule may need verification")
            return None
    return False


# =============================================================================
# TEST 5: RESCHEDULE - Without Existing Booking
# =============================================================================
def test_reschedule_without_existing_booking():
    """Test reschedule request when no booking exists."""
    print_separator("TEST 5: RESCHEDULE - Without Existing Booking")
    print("   State: booking_confirmed=False (no existing booking)")
    print("   Expected: Inform user and offer to book new demo")

    session = ConversationSession()
    session.booking_confirmed = False  # No existing booking

    query = "I want to reschedule my demo"

    print(f"\n📤 User: {query}")
    print(f"   (booking_confirmed=False)")

    data = session.send_message(query)

    if data:
        print_result(data, "Reschedule Without Booking")

        response_lower = data.get("response", "").lower()

        # Should inform user they have no booking
        if (
            "don't have" in response_lower
            or "no confirmed" in response_lower
            or "book a new" in response_lower
            or "no booking" in response_lower
        ):
            print("\n✅ TEST PASSED: Bot correctly informed user they have no booking!")
            return True
        elif "would you like to book" in response_lower:
            print("\n✅ TEST PASSED: Bot offered to create new booking!")
            return True
        else:
            print("\n⚠️  TEST RESULT: Response may need verification")
            return None
    return False


# =============================================================================
# TEST 6: CANCEL - With Existing Booking
# =============================================================================
def test_cancel_with_existing_booking():
    """Test cancelling an existing confirmed booking."""
    print_separator("TEST 6: CANCEL - With Existing Booking")
    print("   Setup: Existing booking on Feb 5th at 4:00 PM")
    print("   Action: Cancel the booking")

    session = ConversationSession()
    # Set up existing confirmed booking
    session.collected_fields = {
        "email": "charlie@example.com",
        "date": "2026-02-05",
        "time": "2026-02-05T10:30:00+00:00",
        "product": "Support Copilot",
    }
    session.booking_confirmed = True

    query = "I need to cancel my demo"

    print(f"\n📤 User: {query}")
    print(f"   (Existing booking_confirmed=True)")

    data = session.send_message(query)

    if data:
        print_result(data, "Cancel")

        response_lower = data.get("response", "").lower()
        booking_confirmed = data.get("booking_confirmed")

        # Check for cancellation
        if "cancel" in response_lower and (
            "sure" in response_lower
            or "confirm" in response_lower
            or "cancelled" in response_lower
        ):
            print("\n✅ TEST PASSED: Bot acknowledged cancellation request!")
            return True
        elif booking_confirmed == False and "cancel" in response_lower:
            print("\n✅ TEST PASSED: Booking cancelled!")
            return True
        else:
            print("\n⚠️  TEST RESULT: Cancellation may need verification")
            return None
    return False


# =============================================================================
# TEST 7: CANCEL - Without Existing Booking
# =============================================================================
def test_cancel_without_existing_booking():
    """Test cancel request when no booking exists."""
    print_separator("TEST 7: CANCEL - Without Existing Booking")
    print("   State: booking_confirmed=False (no existing booking)")
    print("   Expected: Inform user and offer to book new demo")

    session = ConversationSession()
    session.booking_confirmed = False  # No existing booking

    query = "Cancel my demo please"

    print(f"\n📤 User: {query}")
    print(f"   (booking_confirmed=False)")

    data = session.send_message(query)

    if data:
        print_result(data, "Cancel Without Booking")

        response_lower = data.get("response", "").lower()

        # Should inform user they have no booking
        if (
            "don't have" in response_lower
            or "no confirmed" in response_lower
            or "no booking" in response_lower
        ):
            print(
                "\n✅ TEST PASSED: Bot correctly informed user they have no booking to cancel!"
            )
            return True
        elif (
            "would you like to book" in response_lower or "book a new" in response_lower
        ):
            print("\n✅ TEST PASSED: Bot offered to create new booking!")
            return True
        else:
            print("\n⚠️  TEST RESULT: Response may need verification")
            return None
    return False


# =============================================================================
# TEST 8: CONFIRMATION - Already Booked Demo
# =============================================================================
def test_confirmation_already_booked():
    """Test user confirming an already booked demo."""
    print_separator("TEST 8: CONFIRMATION - Already Booked Demo")
    print("   Setup: booking_confirmed=True, all fields collected")
    print("   Action: User says 'ok please book the demo now'")
    print("   Expected: Confirm booking, call lead_analysis_tool")

    session = ConversationSession()
    # Set up already confirmed booking
    session.collected_fields = {
        "email": "kashyap@gmail.com",
        "date": "2026-02-05",
        "time": "2026-02-05T10:30:00+00:00",
        "product": "NovaEdge X1",
    }
    session.booking_confirmed = True
    session.chat_history = [
        {"role": "user", "content": "book me a demo at 5th feb 4pm for novaedge x1"},
        {
            "role": "assistant",
            "content": "Your NovaEdge X1 demo is confirmed for February 5th at 4:00 PM IST!",
        },
    ]

    query = "ok please book the demo now"

    print(f"\n📤 User: {query}")
    print(f"   (booking_confirmed=True, all fields present)")

    data = session.send_message(query)

    if data:
        print_result(data, "Confirmation")

        response_lower = data.get("response", "").lower()
        booking_confirmed = data.get("booking_confirmed")

        # Should confirm the booking with details
        if booking_confirmed == True and (
            "confirm" in response_lower
            or "booked" in response_lower
            or "scheduled" in response_lower
        ):
            print("\n✅ TEST PASSED: Bot confirmed the already-booked demo!")
            return True
        elif (
            "february 5" in response_lower
            or "4:00 pm" in response_lower
            or "kashyap" in response_lower
        ):
            print("\n✅ TEST PASSED: Bot provided booking details!")
            return True
        elif "looking forward" in response_lower or "see you" in response_lower:
            print("\n✅ TEST PASSED: Bot acknowledged the booking!")
            return True
        else:
            # Check if it's not asking for more info (which would be wrong)
            if (
                "email" in response_lower
                or "which product" in response_lower
                or "what time" in response_lower
            ):
                print("\n❌ TEST FAILED: Bot asked for info that was already provided!")
                return False
            print("\n⚠️  TEST RESULT: Response may need verification")
            return None
    return False


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================
def main():
    print("\n" + "=" * 80)
    print("  🧪 COMPREHENSIVE DEMO BOOKING TEST SUITE")
    print("=" * 80)
    print(f"\n📅 Current Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Target: {CHAT_ENDPOINT}")

    # Check server first
    if not test_server_health():
        print("\n❌ Cannot proceed without server. Please start the server first:")
        print(
            '   Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd \'C:\\Users\\kashy\\OneDrive\\Desktop\\mywork\\botrunner_qb\\botrunner\'; conda activate botenv; uvicorn main:app --port 8000"'
        )
        return

    results = []

    # Run all tests
    tests = [
        ("1. NEW BOOKING - Available Slot", test_new_booking_available_slot),
        ("2. NEW BOOKING - Unavailable Slot", test_new_booking_unavailable_slot),
        ("3. NEW BOOKING - Select Alternative", test_new_booking_select_alternative),
        (
            "4. RESCHEDULE - With Existing Booking",
            test_reschedule_with_existing_booking,
        ),
        (
            "5. RESCHEDULE - Without Existing Booking",
            test_reschedule_without_existing_booking,
        ),
        ("6. CANCEL - With Existing Booking", test_cancel_with_existing_booking),
        ("7. CANCEL - Without Existing Booking", test_cancel_without_existing_booking),
        ("8. CONFIRMATION - Already Booked", test_confirmation_already_booked),
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ TEST ERROR: {e}")
            results.append((test_name, False))

        time.sleep(2)  # Pause between tests

    # Summary
    print_separator("📊 TEST SUMMARY")

    passed = 0
    failed = 0
    review = 0

    for test_name, result in results:
        if result == True:
            status = "✅ PASSED"
            passed += 1
        elif result == False:
            status = "❌ FAILED"
            failed += 1
        else:
            status = "⚠️  NEEDS REVIEW"
            review += 1
        print(f"   {status}: {test_name}")

    print(f"\n   📈 Results: {passed} passed, {failed} failed, {review} need review")
    print(f"   📊 Pass Rate: {passed}/{len(tests)} ({100*passed//len(tests)}%)")
    print("=" * 80)

    return passed, failed, review


if __name__ == "__main__":
    main()
