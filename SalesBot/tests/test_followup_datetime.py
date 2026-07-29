"""Test script to verify comprehensive datetime parsing in followup tool"""

import sys
import os
from datetime import datetime, timedelta
import pytz
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_datetime_expression(datetime_expression: str, timezone: str):
    """
    Simplified version of the parsing logic from process_followup_datetime
    for testing without the decorator
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        target = None
        has_time = False
        hour = 14  # Default 2 PM
        minute = 0

        text = datetime_expression.lower().strip()
        text_no_comma = text.replace(",", "")

        # Time extraction patterns
        match_ampm = re.search(r"(\d{1,2}):?(\d{2})?\s*(am|pm)", text, re.IGNORECASE)
        match_24 = re.search(r"(\d{1,2}):(\d{2})", text)

        # Time-of-day map
        time_of_day_map = {
            "noon": (12, 0),
            "midnight": (0, 0),
            "morning": (10, 0),
            "afternoon": (14, 0),
            "evening": (18, 0),
            "night": (20, 0),
            "lunch": (12, 30),
        }

        for time_word, (h, m) in time_of_day_map.items():
            if time_word in text:
                hour = h
                minute = m
                has_time = True
                break

        # Override with explicit time if found
        if match_ampm and not has_time:
            hour = int(match_ampm.group(1))
            minute = int(match_ampm.group(2)) if match_ampm.group(2) else 0
            am_pm = match_ampm.group(3).lower()
            if am_pm == "pm" and hour < 12:
                hour += 12
            elif am_pm == "am" and hour == 12:
                hour = 0
            has_time = True
        elif match_24 and not has_time:
            h = int(match_24.group(1))
            if 0 <= h <= 23:
                hour = h
                minute = int(match_24.group(2))
                has_time = True

        # Handle "in X hours/minutes/days/weeks"
        rel_match = re.search(r"in\s+(\d+)\s+(minute|hour|day|week)s?", text)
        if rel_match:
            amount = int(rel_match.group(1))
            unit = rel_match.group(2)
            delta = timedelta(**{unit + "s": amount})
            target = now + delta

        # Handle "tomorrow"
        elif "tomorrow" in text:
            target = now + timedelta(days=1)
            if has_time:
                target = target.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            else:
                target = target.replace(hour=14, minute=0, second=0, microsecond=0)

        # Handle "today"
        elif "today" in text:
            target = now
            if has_time:
                target = target.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            else:
                target = now + timedelta(hours=1)

        # Handle "next week"
        elif "next week" in text:
            target = now + timedelta(days=7)
            if has_time:
                target = target.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            else:
                target = target.replace(hour=14, minute=0, second=0, microsecond=0)

        # Handle explicit dates
        elif not target:
            date_patterns = [
                r"(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*(\d{4})?",
                r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?\s*(\d{4})?",
                r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})",
                r"(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})",
            ]

            month_map = {
                "jan": 1,
                "feb": 2,
                "mar": 3,
                "apr": 4,
                "may": 5,
                "jun": 6,
                "jul": 7,
                "aug": 8,
                "sep": 9,
                "oct": 10,
                "nov": 11,
                "dec": 12,
                "january": 1,
                "february": 2,
                "march": 3,
                "april": 4,
                "june": 6,
                "july": 7,
                "august": 8,
                "september": 9,
                "october": 10,
                "november": 11,
                "december": 12,
            }

            for pattern in date_patterns:
                match = re.search(pattern, text_no_comma)
                if match:
                    groups = match.groups()
                    year = None
                    month = None
                    day = None

                    if len(groups) == 3 and groups[1] in month_map:
                        day = int(groups[0])
                        month = month_map[groups[1]]
                        year = int(groups[2]) if groups[2] else None
                    elif len(groups) == 3 and groups[0] in month_map:
                        month = month_map[groups[0]]
                        day = int(groups[1])
                        year = int(groups[2]) if groups[2] else None
                    elif (
                        len(groups) == 3 and groups[0].isdigit() and len(groups[0]) <= 2
                    ):
                        day = int(groups[0])
                        month = int(groups[1])
                        year = int(groups[2])
                    elif len(groups) == 3 and len(groups[0]) == 4:
                        year = int(groups[0])
                        month = int(groups[1])
                        day = int(groups[2])

                    if year is None:
                        year = now.year
                        if month < now.month or (month == now.month and day < now.day):
                            year = now.year + 1

                    if day and month and year:
                        try:
                            target = now.replace(
                                year=year,
                                month=month,
                                day=day,
                                hour=14,
                                minute=0,
                                second=0,
                                microsecond=0,
                            )
                            if has_time:
                                target = target.replace(hour=hour, minute=minute)
                            break
                        except ValueError:
                            continue

        # Handle weekday references
        if not target:
            days_of_week = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
            for i, day_name in enumerate(days_of_week):
                if day_name in text:
                    current_weekday = now.weekday()
                    target_weekday = i
                    days_ahead = (target_weekday - current_weekday) % 7

                    if "next" in text or days_ahead == 0:
                        days_ahead = 7 if days_ahead == 0 else days_ahead

                    target = now + timedelta(days=days_ahead)
                    if has_time:
                        target = target.replace(
                            hour=hour, minute=minute, second=0, microsecond=0
                        )
                    else:
                        target = target.replace(
                            hour=14, minute=0, second=0, microsecond=0
                        )
                    break

        if target is None:
            return {"success": False, "error": "Could not parse"}

        utc_target = target.astimezone(pytz.UTC)

        return {
            "success": True,
            "date": target.strftime("%Y-%m-%d"),
            "time": target.strftime("%H:%M"),
            "utc_time_iso": utc_target.isoformat(),
            "local_time_readable": target.strftime("%A, %B %d at %I:%M %p"),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def test_datetime_parsing():
    """Test various datetime expressions"""

    test_cases = [
        # Relative times
        ("in 30 minutes", "America/New_York"),
        ("in 2 hours", "Asia/Kolkata"),
        ("in 3 days", "Europe/London"),
        # Tomorrow/today
        ("tomorrow at 3 PM", "America/New_York"),
        ("today at 5pm", "Asia/Kolkata"),
        # Weekdays
        ("next Monday", "America/New_York"),
        ("this Friday at 12:00 pm", "Asia/Kolkata"),
        ("Friday evening", "Europe/London"),
        # Explicit dates with month names
        ("December 25 at 3pm", "America/New_York"),
        ("9th December at 2:30 PM", "Asia/Kolkata"),
        ("Feb 10 at 3pm", "America/New_York"),
        ("25 dec 2025", "Europe/London"),
        # Numeric dates (DD/MM/YYYY format)
        ("25/12/2025", "America/New_York"),
        ("2025-12-09", "Asia/Kolkata"),
        # Time of day references
        ("tomorrow morning", "America/New_York"),
        ("next week noon", "Asia/Kolkata"),
        ("Friday afternoon", "Europe/London"),
        # Next week
        ("next week at 2pm", "America/New_York"),
    ]

    print("Testing Comprehensive Datetime Parsing for Followup Tool")
    print("=" * 70)

    for expression, timezone in test_cases:
        print(f"\nTesting: '{expression}' with timezone '{timezone}'")
        print("-" * 70)

        try:
            result = parse_datetime_expression(expression, timezone)

            if result.get("success"):
                print(f"✓ SUCCESS")
                print(f"  Date: {result.get('date')}")
                print(f"  Time: {result.get('time')}")
                print(f"  UTC: {result.get('utc_time_iso')}")
                print(f"  Readable: {result.get('local_time_readable')}")
            else:
                print(f"✗ FAILED")
                print(f"  Message: {result.get('message')}")
                print(f"  Error: {result.get('error')}")
        except Exception as e:
            print(f"✗ EXCEPTION: {str(e)}")

    print("\n" + "=" * 70)
    print("Test completed!")


if __name__ == "__main__":
    test_datetime_parsing()
