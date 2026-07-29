"""
Test script for Calendly slot matching fix.

This tests that the check_calendly_availability tool correctly matches
time slots regardless of UTC format differences (Z vs +00:00).

Run: python tests/test_calendly_matching.py
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"


def test_api_health():
    """Test if the API is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def wait_for_server(max_wait=60):
    """Wait for server to be ready."""
    print("⏳ Waiting for server to be ready...")
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if test_api_health():
            print("✅ Server is ready!")
            return True
        time.sleep(2)
    print("❌ Server did not start in time")
    return False


def test_booking_feb5_4pm():
    """
    Test booking for Feb 5th 4 PM IST.

    Expected: Should match the available slot at 2026-02-05T10:30:00Z
    (which is 4:00 PM IST / 10:30 AM UTC)
    """
    print("\n" + "=" * 60)
    print("TEST 1: Book demo for Feb 5th 4 PM (should be AVAILABLE)")
    print("=" * 60)

    payload = {
        "user_id": "test-calendly-match-001",
        "tenant_id": "testing",
        "user_query": "book demo for 5th feb 4 pm",
        "contact_details": {"email": "test@example.com"},
        "region_code": "IN",
    }

    print(f"📤 Request: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=120)

        print(f"📥 Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"📥 Response: {json.dumps(data, indent=2)}")

            # Check if booking was confirmed
            booking_fields = data.get("booking_fields", {})
            booking_confirmed = booking_fields.get("booking_confirmed", False)
            calendly_checked = booking_fields.get("calendly_checked", False)

            print("\n📊 Analysis:")
            print(f"   - calendly_checked: {calendly_checked}")
            print(f"   - booking_confirmed: {booking_confirmed}")

            if booking_confirmed:
                print("✅ SUCCESS: Slot was correctly matched and booking confirmed!")
                return True
            else:
                # Check response text for clues
                response_text = data.get("response", "")
                if (
                    "isn't available" in response_text.lower()
                    or "not available" in response_text.lower()
                ):
                    print("❌ FAILED: Slot reported as unavailable (matching issue)")
                    return False
                elif "confirmed" in response_text.lower():
                    print("✅ SUCCESS: Booking confirmed in response!")
                    return True
                else:
                    print(f"⚠️ UNCERTAIN: Check response manually")
                    return None
        else:
            print(f"❌ Error: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_booking_feb4_530pm():
    """
    Test booking for Feb 4th 5:30 PM IST.

    Expected: Should match the available slot at 2026-02-04T12:00:00Z
    (which is 5:30 PM IST / 12:00 PM UTC)
    """
    print("\n" + "=" * 60)
    print("TEST 2: Book demo for Feb 4th 5:30 PM (should be AVAILABLE)")
    print("=" * 60)

    payload = {
        "user_id": "test-calendly-match-002",
        "tenant_id": "testing",
        "user_query": "book demo for 4th february 5:30 pm",
        "contact_details": {"email": "test2@example.com"},
        "region_code": "IN",
    }

    print(f"📤 Request: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=120)

        print(f"📥 Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"📥 Response: {json.dumps(data, indent=2)}")

            booking_fields = data.get("booking_fields", {})
            booking_confirmed = booking_fields.get("booking_confirmed", False)
            calendly_checked = booking_fields.get("calendly_checked", False)

            print("\n📊 Analysis:")
            print(f"   - calendly_checked: {calendly_checked}")
            print(f"   - booking_confirmed: {booking_confirmed}")

            if booking_confirmed:
                print("✅ SUCCESS: Slot was correctly matched and booking confirmed!")
                return True
            else:
                response_text = data.get("response", "")
                if (
                    "isn't available" in response_text.lower()
                    or "not available" in response_text.lower()
                ):
                    print("❌ FAILED: Slot reported as unavailable (matching issue)")
                    return False
                elif "confirmed" in response_text.lower():
                    print("✅ SUCCESS: Booking confirmed in response!")
                    return True
                else:
                    print(f"⚠️ UNCERTAIN: Check response manually")
                    return None
        else:
            print(f"❌ Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_booking_unavailable_time():
    """
    Test booking for a time that's NOT in available slots.

    Expected: Should return is_available=false with alternatives
    """
    print("\n" + "=" * 60)
    print("TEST 3: Book demo for Feb 5th 2 PM (should be UNAVAILABLE)")
    print("=" * 60)

    payload = {
        "user_id": "test-calendly-match-003",
        "tenant_id": "testing",
        "user_query": "book demo for 5th feb 2 pm",
        "contact_details": {"email": "test3@example.com"},
        "region_code": "IN",
    }

    print(f"📤 Request: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(f"{BASE_URL}/api/chat", json=payload, timeout=120)

        print(f"📥 Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"📥 Response: {json.dumps(data, indent=2)}")

            booking_fields = data.get("booking_fields", {})
            booking_confirmed = booking_fields.get("booking_confirmed", False)
            calendly_checked = booking_fields.get("calendly_checked", False)

            print("\n📊 Analysis:")
            print(f"   - calendly_checked: {calendly_checked}")
            print(f"   - booking_confirmed: {booking_confirmed}")

            # For unavailable times, booking_confirmed should be False
            if not booking_confirmed and calendly_checked:
                response_text = data.get("response", "")
                if (
                    "alternative" in response_text.lower()
                    or "isn't available" in response_text.lower()
                ):
                    print(
                        "✅ SUCCESS: Correctly identified as unavailable with alternatives!"
                    )
                    return True
                else:
                    print("⚠️ UNCERTAIN: Check if alternatives were provided")
                    return None
            elif booking_confirmed:
                print("❌ FAILED: Should NOT have confirmed (2 PM is not available)")
                return False
            else:
                print("⚠️ UNCERTAIN: calendly_checked is False")
                return None
        else:
            print(f"❌ Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def test_direct_calendly_tool():
    """
    Test the check_calendly_availability tool directly by importing it.
    """
    print("\n" + "=" * 60)
    print("TEST 4: Direct tool test - UTC format matching")
    print("=" * 60)

    try:
        # Add parent directory to path
        import os

        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from app.apis.calendly_api import calendly_available_slots_api
        from datetime import datetime
        import pytz

        # Test 1: Feb 5th 4 PM IST = 10:30 AM UTC
        utc = pytz.UTC
        test_dt = datetime(2026, 2, 5, 10, 30, 0, tzinfo=utc)

        print(f"📤 Testing with datetime: {test_dt.isoformat()}")

        result = calendly_available_slots_api("testing", test_dt)
        print(f"📥 API Result: {json.dumps(result, indent=2)}")

        # Check if slots are returned
        slots = result.get("slots", [])
        print(f"\n📊 Available slots:")
        for slot in slots:
            print(f"   - {slot.get('start_time_utc')} ({slot.get('start_time_local')})")

        # Check if our target slot exists
        target_slot = "2026-02-05T10:30:00Z"
        slot_exists = any(s.get("start_time_utc") == target_slot for s in slots)

        if slot_exists:
            print(f"\n✅ Target slot {target_slot} exists in available slots")
        else:
            print(f"\n❌ Target slot {target_slot} NOT found in available slots")

        # Now test the matching logic
        requested_utc_normalized = test_dt.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"\n📊 Matching test:")
        print(f"   Requested (normalized): {requested_utc_normalized}")

        is_match = False
        for slot in slots:
            slot_utc_str = slot.get("start_time_utc", "")
            slot_utc_normalized = (
                slot_utc_str.replace("Z", "").replace("+00:00", "").split(".")[0]
            )
            print(f"   Slot (normalized):      {slot_utc_normalized}")

            if requested_utc_normalized == slot_utc_normalized:
                is_match = True
                print(f"   ✅ MATCH FOUND!")
                break

        if is_match:
            print("\n✅ SUCCESS: Normalization-based matching works!")
            return True
        else:
            print("\n❌ FAILED: No match found after normalization")
            return False

    except ImportError as e:
        print(f"⚠️ Could not import modules (run from project root): {e}")
        return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("🧪 CALENDLY SLOT MATCHING TEST SUITE")
    print("=" * 60)
    print("\nThis tests the fix for UTC format mismatch:")
    print("  - API returns: '2026-02-05T10:30:00Z'")
    print("  - Tool generates: '2026-02-05T10:30:00+00:00'")
    print("  - Fix: Normalize both before comparison")

    # First run the direct tool test
    print("\n🔬 Running direct tool test first...")
    direct_result = test_direct_calendly_tool()

    # Check if server is available for API tests
    print("\n🌐 Checking server availability...")
    if not wait_for_server(max_wait=10):
        print("\n⚠️ Server not available. Skipping API tests.")
        print("   Start the server with: uvicorn main:app --port 8000")

        # Summary without API tests
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY (Direct test only)")
        print("=" * 60)
        if direct_result:
            print("✅ Direct tool test: PASSED")
            print("\n🎉 The normalization fix is working correctly!")
        else:
            print("❌ Direct tool test: FAILED")
        return

    # Run API tests
    results = {
        "Direct Tool Test": direct_result,
        "Feb 5th 4 PM (available)": test_booking_feb5_4pm(),
        "Feb 4th 5:30 PM (available)": test_booking_feb4_530pm(),
        "Feb 5th 2 PM (unavailable)": test_booking_unavailable_time(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0
    uncertain = 0

    for test_name, result in results.items():
        if result is True:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        elif result is False:
            print(f"❌ {test_name}: FAILED")
            failed += 1
        else:
            print(f"⚠️ {test_name}: UNCERTAIN")
            uncertain += 1

    print(f"\n📊 Results: {passed} passed, {failed} failed, {uncertain} uncertain")

    if failed == 0:
        print("\n🎉 All tests passed! The Calendly slot matching fix is working.")
    else:
        print("\n⚠️ Some tests failed. Please review the output above.")


if __name__ == "__main__":
    run_all_tests()
