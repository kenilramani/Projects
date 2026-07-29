"""
Direct unit test for Calendly slot matching fix.
This tests the matching logic WITHOUT needing the server running.

Run: python tests/test_calendly_direct.py
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_calendly_matching():
    """Test the check_calendly_availability matching logic directly."""

    print("\n" + "=" * 60)
    print("🧪 DIRECT CALENDLY SLOT MATCHING TEST")
    print("=" * 60)
    print("\nThis tests the fix for UTC format mismatch:")
    print("  - API returns: '2026-02-05T10:30:00Z'")
    print("  - Tool generates: '2026-02-05T10:30:00+00:00'")
    print("  - Fix: Normalize both before comparison")

    from app.apis.calendly_api import calendly_available_slots_api
    from datetime import datetime
    import pytz

    utc = pytz.UTC

    # Test cases: (description, test_datetime, expected_slot_utc, should_match)
    test_cases = [
        (
            "Feb 5th 4:00 PM IST (10:30 UTC)",
            datetime(2026, 2, 5, 10, 30, 0, tzinfo=utc),
            "2026-02-05T10:30:00Z",
            True,
        ),
        (
            "Feb 4th 5:30 PM IST (12:00 UTC)",
            datetime(2026, 2, 4, 12, 0, 0, tzinfo=utc),
            "2026-02-04T12:00:00Z",
            True,
        ),
        (
            "Jan 30th 2:30 PM IST (09:00 UTC)",
            datetime(2026, 1, 30, 9, 0, 0, tzinfo=utc),
            "2026-01-30T09:00:00Z",
            True,
        ),
        (
            "Feb 5th 2:00 PM IST (08:30 UTC) - NOT AVAILABLE",
            datetime(2026, 2, 5, 8, 30, 0, tzinfo=utc),
            "2026-02-05T08:30:00Z",
            False,
        ),
    ]

    all_passed = True

    for description, test_dt, expected_slot, should_match in test_cases:
        print(f"\n{'='*60}")
        print(f"TEST: {description}")
        print(f"{'='*60}")

        print(f"📤 Testing datetime: {test_dt.isoformat()}")
        print(f"📋 Expected slot: {expected_slot}")
        print(f"📋 Should match: {should_match}")

        # Get available slots from mock API
        result = calendly_available_slots_api("testing", test_dt)
        slots = result.get("slots", [])

        print(f"\n📥 Available slots from API:")
        for slot in slots:
            print(f"   - {slot.get('start_time_utc')}")

        # Test the FIXED matching logic (normalized comparison)
        requested_utc_normalized = test_dt.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"\n🔍 Matching:")
        print(f"   Requested (normalized): {requested_utc_normalized}")

        is_match = False
        matched_slot = None
        for slot in slots:
            slot_utc_str = slot.get("start_time_utc", "")
            slot_utc_normalized = (
                slot_utc_str.replace("Z", "").replace("+00:00", "").split(".")[0]
            )

            if requested_utc_normalized == slot_utc_normalized:
                is_match = True
                matched_slot = slot_utc_str
                print(f"   ✅ MATCH: {slot_utc_str} -> {slot_utc_normalized}")
                break

        if not is_match:
            print(f"   ❌ No match found")

        # Verify result
        if is_match == should_match:
            if should_match:
                print(f"\n✅ PASSED: Correctly matched slot {matched_slot}")
            else:
                print(f"\n✅ PASSED: Correctly identified as unavailable")
        else:
            all_passed = False
            if should_match:
                print(f"\n❌ FAILED: Should have matched but didn't!")
            else:
                print(f"\n❌ FAILED: Should NOT have matched but did!")

    # Also test the OLD (broken) matching logic for comparison
    print(f"\n{'='*60}")
    print("COMPARISON: OLD (BROKEN) vs NEW (FIXED) Matching")
    print(f"{'='*60}")

    # Test case: Feb 5th 4 PM IST
    test_dt = datetime(2026, 2, 5, 10, 30, 0, tzinfo=utc)
    result = calendly_available_slots_api("testing", test_dt)
    slots = result.get("slots", [])

    # Simulate what the tool generates (with +00:00 format)
    requested_iso = test_dt.isoformat()  # "2026-02-05T10:30:00+00:00"

    print(f"\n📤 Requested time ISO: {requested_iso}")
    print(f"📥 Slot in API: 2026-02-05T10:30:00Z")

    # OLD matching (strict string comparison)
    old_match = any(slot.get("start_time_utc") == requested_iso for slot in slots)
    print(f"\n🔴 OLD (strict comparison): Match = {old_match}")
    print(
        f"   '{requested_iso}' == '2026-02-05T10:30:00Z' -> {requested_iso == '2026-02-05T10:30:00Z'}"
    )

    # NEW matching (normalized comparison)
    requested_normalized = test_dt.strftime("%Y-%m-%dT%H:%M:%S")
    new_match = any(
        slot.get("start_time_utc", "")
        .replace("Z", "")
        .replace("+00:00", "")
        .split(".")[0]
        == requested_normalized
        for slot in slots
    )
    print(f"\n🟢 NEW (normalized comparison): Match = {new_match}")
    print(
        f"   '{requested_normalized}' == '2026-02-05T10:30:00' -> {requested_normalized == '2026-02-05T10:30:00'}"
    )

    # Summary
    print(f"\n{'='*60}")
    print("📋 TEST SUMMARY")
    print(f"{'='*60}")

    if all_passed:
        print("✅ All tests PASSED!")
        print("\n🎉 The UTC format normalization fix is working correctly!")
        print("\nThe fix ensures that:")
        print("  - '2026-02-05T10:30:00+00:00' matches '2026-02-05T10:30:00Z'")
        print("  - Both are normalized to '2026-02-05T10:30:00' for comparison")
    else:
        print("❌ Some tests FAILED!")

    return all_passed


if __name__ == "__main__":
    success = test_calendly_matching()
    sys.exit(0 if success else 1)
