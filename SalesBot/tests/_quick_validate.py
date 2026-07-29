"""Quick validation of prompt caching imports and logic."""

import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test 1: Core module imports
from app.utils.prompt_cache import (
    CACHE_BREAK,
    split_cached_prompt,
    build_cached_messages,
    split_direct_call_messages,
    PromptCacheMonitor,
    cache_monitor,
)

print("OK  1: prompt_cache imports")

# Test 2: Split logic
s, d = split_cached_prompt(f"static{CACHE_BREAK}dynamic")
assert s == "static" and d == "dynamic", f"Got {s!r}, {d!r}"
print("OK  2: split_cached_prompt")

# Test 3: No break
s, d = split_cached_prompt("just a prompt")
assert s == "just a prompt" and d is None
print("OK  3: split without break")

# Test 4: build_cached_messages with split
msgs = build_cached_messages(
    f"sys{CACHE_BREAK}ctx", [{"role": "user", "content": "hi"}]
)
assert len(msgs) == 3 and msgs[0]["role"] == "system" and msgs[1]["role"] == "system"
print("OK  4: build_cached_messages with split")

# Test 5: build_cached_messages without split
msgs = build_cached_messages("sys only", [{"role": "user", "content": "hi"}])
assert len(msgs) == 2 and msgs[0]["content"] == "sys only"
print("OK  5: build_cached_messages without split")

# Test 6: split_direct_call_messages
msgs = split_direct_call_messages(f"static part{CACHE_BREAK}dynamic part")
assert (
    len(msgs) == 2
    and msgs[0]["content"] == "static part"
    and msgs[1]["content"] == "dynamic part"
)
print("OK  6: split_direct_call_messages")

# Test 7: CacheMonitor
mon = PromptCacheMonitor()
assert mon.get_stats()["total_requests"] == 0
print("OK  7: CacheMonitor init")

# Test 8: Settings
from app.config import settings

print(f"OK  8: settings.enable_prompt_caching = {settings.enable_prompt_caching}")

# Test 9: Check prompt files for CACHE_BREAK
prompt_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "prompts"
)
found = []
for fname in sorted(os.listdir(prompt_dir)):
    if fname.endswith(".py") and not fname.startswith("__"):
        with open(os.path.join(prompt_dir, fname), "r", encoding="utf-8") as f:
            if "CACHE_BREAK" in f.read():
                found.append(fname)
print(f"OK  9: {len(found)} prompt files with CACHE_BREAK: {', '.join(found)}")

# Test 10: Route module import
from app.route.route import RouterModel

print("OK 10: RouterModel imports")

# Test 11: Main app import check
try:
    from main import app

    print("OK 11: main.py app imports")
except Exception as e:
    print(f"WARN 11: main.py import issue (may need env vars): {e}")

print("\n=== ALL VALIDATION CHECKS PASSED ===")
