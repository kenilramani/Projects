"""
Prompt Caching Test Script - Validates cache effectiveness and cost savings.

This script:
1. Starts multiple chat requests with identical personas (static prompt prefix)
2. Monitors OpenAI's automatic prompt caching via response usage metrics
3. Reports cache hit rates, token savings, and cost reduction
4. Validates that caching doesn't break existing functionality

Usage:
    # First start the server:
    # cd C:\\Users\\kashy\\OneDrive\\Desktop\\mywork\\botrunner_qb\\botrunner
    # conda activate botenv
    # uvicorn main:app --port 8000
    
    # Then run tests:
    # conda activate botenv
    # python tests/test_prompt_caching.py

Requirements:
    - Server running on http://localhost:8000
    - Valid API keys configured in .env
"""

import asyncio
import time
import json
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx


from app.config.settings import logger


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "http://localhost:8000"
TEST_USER_ID = "cache_test_user_001"
TEST_TENANT_ID = "cache_test_tenant"

# Model pricing per 1M tokens (in USD)
# Source: Provided pricing table
MODEL_PRICING = {
    # GPT-5 series
    "gpt-5.2": {"input": 1.75, "cached": 0.175, "output": 14.00},
    "gpt-5.1": {"input": 1.25, "cached": 0.125, "output": 10.00},
    "gpt-5": {"input": 1.25, "cached": 0.125, "output": 10.00},
    "gpt-5-mini": {"input": 0.25, "cached": 0.025, "output": 2.00},
    "gpt-5-nano": {"input": 0.05, "cached": 0.005, "output": 0.40},
    "gpt-5.2-chat-latest": {"input": 1.75, "cached": 0.175, "output": 14.00},
    "gpt-5.1-chat-latest": {"input": 1.25, "cached": 0.125, "output": 10.00},
    "gpt-5-chat-latest": {"input": 1.25, "cached": 0.125, "output": 10.00},
    "gpt-5.2-codex": {"input": 1.75, "cached": 0.175, "output": 14.00},
    "gpt-5.1-codex-max": {"input": 1.25, "cached": 0.125, "output": 10.00},
    "gpt-5.1-codex": {"input": 1.25, "cached": 0.125, "output": 10.00},
    "gpt-5-codex": {"input": 1.25, "cached": 0.125, "output": 10.00},
    "gpt-5.2-pro": {
        "input": 21.00,
        "cached": 21.00,
        "output": 168.00,
    },  # No cached discount
    "gpt-5-pro": {
        "input": 15.00,
        "cached": 15.00,
        "output": 120.00,
    },  # No cached discount
    # GPT-4.1 series
    "gpt-4.1": {"input": 2.00, "cached": 0.50, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "cached": 0.10, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "cached": 0.025, "output": 0.40},
    "gpt-4o": {"input": 2.50, "cached": 1.25, "output": 10.00},
    "gpt-4o-mini": {"input": 0.40, "cached": 0.10, "output": 1.60},  # Guardrail model
    # Azure models (same pricing, prefixed)
    "azure/gpt-4.1": {"input": 2.00, "cached": 0.50, "output": 8.00},
    "azure/gpt-4.1-mini": {"input": 0.40, "cached": 0.10, "output": 1.60},
    # Default fallback pricing (for unknown models)
    "default": {"input": 1.25, "cached": 0.125, "output": 10.00},
}


def get_model_pricing(model_name: str) -> Dict[str, float]:
    """Get pricing for a model, with fallback to default."""
    # Normalize model name
    model_lower = model_name.lower().strip()

    # Direct mapping for known internal names
    model_mapping = {
        "primary": "gpt-5.1-chat-latest",
        "guardrail": "gpt-4o-mini",
        "summarizer": "gpt-5-nano",
    }

    # Check if it's a known internal name
    if model_lower in model_mapping:
        model_lower = model_mapping[model_lower]

    # Try exact match first
    for key in MODEL_PRICING:
        if key.lower() == model_lower:
            return MODEL_PRICING[key]

    # Try partial match (e.g., "azure/gpt-4.1" contains "gpt-4.1")
    for key in MODEL_PRICING:
        if key in model_lower or model_lower in key:
            return MODEL_PRICING[key]

    # Default fallback
    return MODEL_PRICING["default"]


# Test persona (stays constant across all requests for maximum cache hits)
TEST_PERSONA = {
    "name": "CacheBot",
    "industry": "Technology",
    "category": "Software Solutions",
    "sub_category": "AI Automation",
    "business_type": "B2B SaaS",
    "company_name": "CacheTech AI",
    "company_domain": "cachetech.ai",
    "company_description": "CacheTech AI provides intelligent automation solutions for enterprise sales and support teams.",
    "company_products": [
        {
            "id": "prod_001",
            "name": "AI Sales Bot",
            "description": "Automated sales conversations with lead qualification",
        },
        {
            "id": "prod_002",
            "name": "Support Copilot",
            "description": "AI-powered customer support assistant",
        },
    ],
    "core_usps": "Fast deployment, high accuracy, enterprise-grade security, 50% cost reduction",
    "core_features": "RAG, Multi-agent orchestration, CRM integration, Real-time analytics",
    "contact_info": "sales@cachetech.ai | +1-555-CACHE-01",
    "language": "en",
    "rules": ["Do not hallucinate pricing", "Escalate to human on legal queries"],
    "offer_description": "Get a free 14-day trial of our AI platform",
    "prompt": "You are a helpful, concise AI sales assistant for CacheTech AI.",
    "personality": "Professional, friendly, persuasive",
    "business_focus": "B2B SaaS sales automation",
    "goal_type": "lead_generation",
    "use_emoji": True,
    "use_name_reference": True,
    "enable_probing": False,
    "current_cta": "book a demo",
}

# Test queries - varied queries with same persona to test prefix caching
TEST_QUERIES = [
    "Hello there!",
    "What products do you offer?",
    "Tell me about your AI Sales Bot",
    "How much does it cost?",
    "What makes you different from competitors?",
    "Can you tell me about enterprise features?",
    "What integrations do you support?",
    "Do you have a free trial?",
    "How does the RAG system work?",
    "I'd like to book a demo please",
]


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class RequestResult:
    """Result from a single test request."""

    query: str
    status_code: int
    response_text: str
    elapsed_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class CacheTestReport:
    """Comprehensive test report."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_elapsed_ms: float = 0.0
    avg_response_ms: float = 0.0
    cache_stats: Dict[str, Any] = field(default_factory=dict)
    request_results: List[RequestResult] = field(default_factory=list)


# =============================================================================
# TEST FUNCTIONS
# =============================================================================


def build_chat_request(user_query: str, user_id: str = TEST_USER_ID) -> Dict:
    """Build a /chat request payload."""
    return {
        "user_context": {
            "user_id": user_id,
            "tenant_id": TEST_TENANT_ID,
            "user_query": user_query,
        },
        "bot_persona": TEST_PERSONA,
    }


async def send_chat_request(
    client: httpx.AsyncClient,
    query: str,
    user_id: str = TEST_USER_ID,
    request_num: int = 0,
) -> RequestResult:
    """Send a single chat request and measure response time."""
    payload = build_chat_request(query, user_id)

    logger.info(f"[Request {request_num}] Sending: '{query}'")
    start = time.perf_counter()

    try:
        response = await client.post(
            f"{BASE_URL}/chat",
            json=payload,
            timeout=60.0,
        )
        elapsed = (time.perf_counter() - start) * 1000

        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            logger.success(
                f"[Request {request_num}] OK in {elapsed:.0f}ms | "
                f"Response: {response_text[:80]}..."
            )
            return RequestResult(
                query=query,
                status_code=200,
                response_text=response_text,
                elapsed_ms=elapsed,
                success=True,
            )
        else:
            error_text = response.text[:200]
            logger.error(
                f"[Request {request_num}] HTTP {response.status_code}: {error_text}"
            )
            return RequestResult(
                query=query,
                status_code=response.status_code,
                response_text="",
                elapsed_ms=elapsed,
                success=False,
                error=error_text,
            )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(f"[Request {request_num}] Error: {e}")
        return RequestResult(
            query=query,
            status_code=0,
            response_text="",
            elapsed_ms=elapsed,
            success=False,
            error=str(e),
        )


async def get_cache_stats(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Fetch cache statistics from the server."""
    try:
        response = await client.get(f"{BASE_URL}/cache_stats", timeout=10.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.warning(f"Could not fetch cache stats: {e}")
    return {}


async def reset_cache_stats(client: httpx.AsyncClient):
    """Reset cache statistics on the server."""
    try:
        response = await client.post(f"{BASE_URL}/cache_stats/reset", timeout=10.0)
        if response.status_code == 200:
            logger.info("Cache statistics reset successfully")
    except Exception as e:
        logger.warning(f"Could not reset cache stats: {e}")


async def check_server_health(client: httpx.AsyncClient) -> bool:
    """Check if the server is running."""
    try:
        response = await client.get(f"{BASE_URL}/health", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================


async def run_cache_tests() -> CacheTestReport:
    """
    Run the full prompt caching test suite.

    Sends multiple requests with the same persona to test:
    1. Cache warming (first request builds cache)
    2. Cache hits (subsequent requests use cached prefix)
    3. Response time improvements
    4. Token cost savings
    """
    report = CacheTestReport()

    async with httpx.AsyncClient() as client:
        # Check server health
        logger.info("=" * 80)
        logger.info("PROMPT CACHING TEST SUITE")
        logger.info("=" * 80)

        if not await check_server_health(client):
            logger.error(
                "Server not reachable at {BASE_URL}. "
                "Start it with: uvicorn main:app --port 8000"
            )
            return report

        logger.success("Server is healthy")

        # Reset cache stats for clean test
        await reset_cache_stats(client)

        # Get initial cache stats
        initial_stats = await get_cache_stats(client)
        logger.info(f"Initial cache stats: {json.dumps(initial_stats, indent=2)}")

        # Phase 1: Cache Warming (first request builds the cache)
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: CACHE WARMING")
        logger.info("First request with this persona - building cache prefix")
        logger.info("=" * 80)

        result = await send_chat_request(client, TEST_QUERIES[0], request_num=1)
        report.request_results.append(result)
        report.total_requests += 1
        if result.success:
            report.successful_requests += 1
        else:
            report.failed_requests += 1
        report.total_elapsed_ms += result.elapsed_ms

        # Small delay to allow cache to settle
        await asyncio.sleep(2)

        # Phase 2: Cache Validation (subsequent requests should hit cache)
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: CACHE VALIDATION")
        logger.info("Sending varied queries with same persona prefix")
        logger.info("=" * 80)

        for i, query in enumerate(TEST_QUERIES[1:], start=2):
            result = await send_chat_request(client, query, request_num=i)
            report.request_results.append(result)
            report.total_requests += 1
            if result.success:
                report.successful_requests += 1
            else:
                report.failed_requests += 1
            report.total_elapsed_ms += result.elapsed_ms

            # Brief delay between requests
            await asyncio.sleep(1)

        # Phase 3: Repeated Query Test (exact same query should have highest cache hit)
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: REPEATED QUERY TEST")
        logger.info("Sending identical queries to maximize cache hits")
        logger.info("=" * 80)

        for i in range(3):
            result = await send_chat_request(
                client,
                "What products do you offer?",
                request_num=len(TEST_QUERIES) + i + 1,
            )
            report.request_results.append(result)
            report.total_requests += 1
            if result.success:
                report.successful_requests += 1
            else:
                report.failed_requests += 1
            report.total_elapsed_ms += result.elapsed_ms
            await asyncio.sleep(1)

        # Fetch final cache stats
        logger.info("\n" + "=" * 80)
        logger.info("COLLECTING RESULTS")
        logger.info("=" * 80)

        final_stats = await get_cache_stats(client)
        report.cache_stats = final_stats
        report.avg_response_ms = (
            report.total_elapsed_ms / report.total_requests
            if report.total_requests > 0
            else 0
        )

    return report


def print_report(report: CacheTestReport):
    """Print a formatted test report with detailed cost analysis."""
    print("\n" + "=" * 100)
    print("PROMPT CACHING TEST REPORT - DETAILED ANALYSIS")
    print("=" * 100)

    # Request Summary
    print(f"\n[REQUEST SUMMARY]")
    print(f"  Total Chat Requests:        {report.total_requests}")
    print(f"  Successful:                 {report.successful_requests}")
    print(f"  Failed:                     {report.failed_requests}")
    print(
        f"  Success Rate:               {(report.successful_requests/max(report.total_requests,1)*100):.1f}%"
    )
    print(f"  Avg Response Time:          {report.avg_response_ms:.0f}ms")
    print(f"  Total Elapsed:              {report.total_elapsed_ms/1000:.1f}s")

    # Cache Statistics
    stats = report.cache_stats
    if stats:
        total_llm = stats.get("total_requests", 0)
        total_prompt = stats.get("total_prompt_tokens", 0)
        total_cached = stats.get("total_cached_tokens", 0)
        total_completion = stats.get("total_completion_tokens", 0)

        print(f"\n[CACHE STATISTICS]")
        print(f"  Total LLM Calls:            {total_llm}")
        print(f"  Total Prompt Tokens:        {total_prompt:,}")
        print(
            f"  Total Cached Tokens:        {total_cached:,} ({stats.get('overall_cache_hit_rate_pct', 0):.1f}%)"
        )
        print(f"  Total Completion Tokens:    {total_completion:,}")
        print(
            f"  Request Cache Hit Rate:     {stats.get('request_cache_hit_rate_pct', 0):.1f}%"
        )
        print(
            f"  Estimated Savings:          {stats.get('estimated_input_cost_savings_pct', 0):.1f}%"
        )

        # Detailed per-model breakdown
        recent = stats.get("recent_requests", [])
        if recent:
            # Group by model
            model_stats = {}
            for r in recent:
                model = r.get("model", "unknown")
                if model not in model_stats:
                    model_stats[model] = {
                        "calls": 0,
                        "prompt_tokens": 0,
                        "cached_tokens": 0,
                        "completion_tokens": 0,
                    }
                model_stats[model]["calls"] += 1
                model_stats[model]["prompt_tokens"] += r.get("total_prompt_tokens", 0)
                model_stats[model]["cached_tokens"] += r.get("cached_tokens", 0)
                model_stats[model]["completion_tokens"] += r.get("completion_tokens", 0)

            print(f"\n[PER-MODEL BREAKDOWN]")
            print(
                f"  {'Model':<20} {'Calls':>6} {'Prompt':>12} {'Cached':>12} {'Output':>12} {'Hit%':>8}"
            )
            print(f"  {'-'*20} {'-'*6} {'-'*12} {'-'*12} {'-'*12} {'-'*8}")

            for model, data in sorted(model_stats.items()):
                hit_rate = (data["cached_tokens"] / max(data["prompt_tokens"], 1)) * 100
                print(
                    f"  {model:<20} "
                    f"{data['calls']:>6} "
                    f"{data['prompt_tokens']:>12,} "
                    f"{data['cached_tokens']:>12,} "
                    f"{data['completion_tokens']:>12,} "
                    f"{hit_rate:>7.1f}%"
                )

            print(
                f"\n[RECENT LLM CALLS - Last {min(len(recent), 20)} of {len(recent)}]"
            )
            print(
                f"  {'#':>3} {'Model':<20} {'Cached':>10} {'Prompt':>10} {'Output':>10} {'Hit%':>8} {'Save%':>8}"
            )
            print(f"  {'-'*3} {'-'*20} {'-'*10} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")

            # Show last 20 calls
            for i, r in enumerate(recent[-20:], 1):
                print(
                    f"  {i:>3} "
                    f"{r.get('model', 'unknown'):<20} "
                    f"{r.get('cached_tokens', 0):>10,} "
                    f"{r.get('total_prompt_tokens', 0):>10,} "
                    f"{r.get('completion_tokens', 0):>10,} "
                    f"{r.get('hit_rate_pct', 0):>7.1f}% "
                    f"{r.get('savings_pct', 0):>7.1f}%"
                )
    else:
        print("\n⚠️  No cache statistics available")

    # Response Times
    successful = [r for r in report.request_results if r.success]
    if successful:
        times = [r.elapsed_ms for r in successful]
        first_time = times[0] if times else 0
        subsequent_avg = sum(times[1:]) / len(times[1:]) if len(times) > 1 else 0
        min_time = min(times) if times else 0
        max_time = max(times) if times else 0

        print(f"\n[RESPONSE TIMES]")
        print(f"  First Request (cache warm):  {first_time:.0f}ms")
        print(f"  Subsequent Average:          {subsequent_avg:.0f}ms")
        print(f"  Fastest:                     {min_time:.0f}ms")
        print(f"  Slowest:                     {max_time:.0f}ms")
        if first_time > 0 and subsequent_avg > 0:
            speedup = ((first_time - subsequent_avg) / first_time) * 100
            print(f"  Latency Change:              {speedup:+.1f}%")

    # Detailed Cost Analysis with actual model pricing
    if stats and stats.get("total_prompt_tokens", 0) > 0:
        recent = stats.get("recent_requests", [])

        # Calculate actual costs per model
        model_costs = {}
        total_cost_without = 0.0
        total_cost_with = 0.0

        for r in recent:
            model = r.get("model", "unknown")
            prompt_tokens = r.get("total_prompt_tokens", 0)
            cached_tokens = r.get("cached_tokens", 0)
            completion_tokens = r.get("completion_tokens", 0)
            uncached_tokens = prompt_tokens - cached_tokens

            # Get pricing for this model
            pricing = get_model_pricing(model)

            # Calculate costs
            cost_without = (
                prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]
            ) / 1_000_000
            cost_with = (
                uncached_tokens * pricing["input"]
                + cached_tokens * pricing["cached"]
                + completion_tokens * pricing["output"]
            ) / 1_000_000

            if model not in model_costs:
                model_costs[model] = {
                    "cost_without": 0.0,
                    "cost_with": 0.0,
                    "savings": 0.0,
                    "calls": 0,
                    "pricing": pricing,
                }

            model_costs[model]["cost_without"] += cost_without
            model_costs[model]["cost_with"] += cost_with
            model_costs[model]["savings"] += cost_without - cost_with
            model_costs[model]["calls"] += 1

            total_cost_without += cost_without
            total_cost_with += cost_with

        total_savings = total_cost_without - total_cost_with
        savings_pct = (total_savings / max(total_cost_without, 0.000001)) * 100

        print(f"\n[DETAILED COST ANALYSIS - Actual Model Pricing]")
        print(
            f"  {'Model':<20} {'Calls':>6} {'Without Cache':>14} {'With Cache':>14} {'Savings':>14} {'Save%':>8}"
        )
        print(f"  {'-'*20} {'-'*6} {'-'*14} {'-'*14} {'-'*14} {'-'*8}")

        for model, data in sorted(
            model_costs.items(), key=lambda x: x[1]["savings"], reverse=True
        ):
            save_pct = (data["savings"] / max(data["cost_without"], 0.000001)) * 100
            pricing = data["pricing"]
            print(
                f"  {model:<20} "
                f"{data['calls']:>6} "
                f"${data['cost_without']:>13.6f} "
                f"${data['cost_with']:>13.6f} "
                f"${data['savings']:>13.6f} "
                f"{save_pct:>7.1f}%"
            )
            print(
                f"       -> Pricing: ${pricing['input']}/M input, ${pricing['cached']}/M cached, ${pricing['output']}/M output"
            )

        print(f"  {'-'*20} {'-'*6} {'-'*14} {'-'*14} {'-'*14} {'-'*8}")
        print(
            f"  {'TOTAL':<20} "
            f"{len(recent):>6} "
            f"${total_cost_without:>13.6f} "
            f"${total_cost_with:>13.6f} "
            f"${total_savings:>13.6f} "
            f"{savings_pct:>7.1f}%"
        )

        # Extrapolation
        if report.total_requests > 0:
            print(f"\n[COST PROJECTIONS]")

            # Per 1000 requests
            cost_per_1k_without = (total_cost_without / len(recent)) * 1000
            cost_per_1k_with = (total_cost_with / len(recent)) * 1000
            savings_per_1k = cost_per_1k_without - cost_per_1k_with

            print(f"  Per 1,000 chat requests:")
            print(f"    Without caching:         ${cost_per_1k_without:>10.2f}")
            print(f"    With caching:            ${cost_per_1k_with:>10.2f}")
            print(
                f"    Savings:                 ${savings_per_1k:>10.2f} ({savings_pct:.1f}%)"
            )

            # Per 10k requests
            print(f"  Per 10,000 chat requests:")
            print(f"    Without caching:         ${cost_per_1k_without*10:>10.2f}")
            print(f"    With caching:            ${cost_per_1k_with*10:>10.2f}")
            print(
                f"    Savings:                 ${savings_per_1k*10:>10.2f} ({savings_pct:.1f}%)"
            )

            # Per 100k requests
            print(f"  Per 100,000 chat requests:")
            print(f"    Without caching:         ${cost_per_1k_without*100:>10.2f}")
            print(f"    With caching:            ${cost_per_1k_with*100:>10.2f}")
            print(
                f"    Savings:                 ${savings_per_1k*100:>10.2f} ({savings_pct:.1f}%)"
            )

    # Individual Request Details
    print(f"\n[CHAT REQUEST DETAILS]")
    print(f"  {'#':>3} {'Status':>7} {'Time':>8} {'Query':<60}")
    print(f"  {'-'*3} {'-'*7} {'-'*8} {'-'*60}")
    for i, r in enumerate(report.request_results, 1):
        status = "[OK]" if r.success else "[FAIL]"
        query_truncated = r.query[:57] + "..." if len(r.query) > 60 else r.query
        print(f"  {i:>3} {status:>7} {r.elapsed_ms:>7.0f}ms {query_truncated:<60}")

    # Success Criteria
    print(f"\n[SUCCESS CRITERIA VALIDATION]")
    all_pass = True

    # Check 1: No breaking changes
    success_rate = report.successful_requests / max(report.total_requests, 1) * 100
    check1 = success_rate >= 90
    print(
        f"  [{'PASS' if check1 else 'FAIL'}] Zero Breaking Changes: {success_rate:.1f}% success (target: >=90%)"
    )
    all_pass = all_pass and check1

    # Check 2: Cache hit rate
    cache_hit_rate = stats.get("request_cache_hit_rate_pct", 0) if stats else 0
    check2 = cache_hit_rate >= 30  # Adjusted target (first run includes cache warming)
    status2 = "PASS" if check2 else ("WARN" if cache_hit_rate > 0 else "FAIL")
    print(f"  [{status2}] Cache Hit Rate: {cache_hit_rate:.1f}% (target: >=30%)")
    all_pass = all_pass and check2

    # Check 3: Cost savings
    cost_savings = stats.get("estimated_input_cost_savings_pct", 0) if stats else 0
    check3 = cost_savings > 0
    print(
        f"  [{'PASS' if check3 else 'WARN'}] Cost Savings: {cost_savings:.1f}% (target: >0%)"
    )
    all_pass = all_pass and check3

    # Check 4: Server running
    check4 = report.total_requests > 0
    print(
        f"  [{'PASS' if check4 else 'FAIL'}] Server Operational: {report.total_requests} requests completed"
    )
    all_pass = all_pass and check4

    # Check 5: Token monitoring
    check5 = stats and stats.get("total_requests", 0) > 0
    print(
        f"  [{'PASS' if check5 else 'FAIL'}] Token Monitoring: {'Active' if check5 else 'Inactive'}"
    )
    all_pass = all_pass and check5

    print(f"\n{'='*100}")
    if all_pass:
        print("*** ALL CHECKS PASSED - Prompt caching is working correctly! ***")
    else:
        print("*** SOME CHECKS NEED ATTENTION - Review the results above ***")
    print("=" * 100)

    # Implementation notes
    print(f"\n[CACHING IMPLEMENTATION NOTES]")
    print(
        f"  - Static prompt prefix (persona, rules, examples) is cached automatically"
    )
    print(
        f"  - Dynamic content (chat history, user data) is sent uncached after CACHE_BREAK"
    )
    print(f"  - OpenAI caches prompts >=1024 tokens with 5-10 minute TTL")
    print(f"  - First request per session = cache miss (cache warming phase)")
    print(f"  - Cached tokens billed at 50-90% discount depending on model")
    print(f"  - Cache hit rates improve with consistent persona + rapid requests")

    if cache_hit_rate < 40:
        print(f"\n[OPTIMIZATION TIPS FOR LOW CACHE HIT RATE]")
        print(f"  - Ensure static prompts are >=1024 tokens")
        print(f"  - Keep requests within 5-10 minute window")
        print(f"  - Use same model endpoint consistently")
        print(f"  - Minimize changes to persona/system instructions")


# =============================================================================
# UNIT TESTS FOR PROMPT SPLITTING
# =============================================================================


def test_prompt_splitting():
    """Test the CACHE_BREAK splitting logic."""
    from app.utils.prompt_cache import (
        CACHE_BREAK,
        split_cached_prompt,
        build_cached_messages,
    )

    print("\n" + "=" * 80)
    print("UNIT TESTS: Prompt Splitting")
    print("=" * 80)

    # Test 1: Split with CACHE_BREAK
    instructions = f"Static instructions here.{CACHE_BREAK}Dynamic context here."
    static, dynamic = split_cached_prompt(instructions)
    assert static == "Static instructions here.", f"Expected static, got: {static}"
    assert dynamic == "Dynamic context here.", f"Expected dynamic, got: {dynamic}"
    print("  [PASS] Test 1: Basic split works")

    # Test 2: No CACHE_BREAK
    instructions = "Just a normal prompt without break."
    static, dynamic = split_cached_prompt(instructions)
    assert static == instructions, f"Expected original, got: {static}"
    assert dynamic is None, f"Expected None, got: {dynamic}"
    print("  [PASS] Test 2: No break returns original")

    # Test 3: Build cached messages with split
    instructions = f"System prompt.{CACHE_BREAK}Dynamic data."
    messages = build_cached_messages(instructions, [{"role": "user", "content": "hi"}])
    assert len(messages) == 3, f"Expected 3 messages, got {len(messages)}"
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "System prompt."
    assert messages[1]["role"] == "system"
    assert messages[1]["content"] == "Dynamic data."
    assert messages[2]["role"] == "user"
    print("  [PASS] Test 3: Build cached messages creates two system messages")

    # Test 4: Build cached messages without split
    messages = build_cached_messages(
        "Just a prompt.", [{"role": "user", "content": "hi"}]
    )
    assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
    assert messages[0]["content"] == "Just a prompt."
    print("  [PASS] Test 4: Build without break creates single system message")

    # Test 5: Build cached messages with caching disabled
    instructions = f"System prompt.{CACHE_BREAK}Dynamic data."
    messages = build_cached_messages(
        instructions, [{"role": "user", "content": "hi"}], enable_caching=False
    )
    assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
    print("  [PASS] Test 5: Caching disabled uses single message")

    # Test 6: Verify prompts contain CACHE_BREAK
    print("\n  Checking prompt files for CACHE_BREAK marker:")
    prompt_files_with_cache_break = []
    prompt_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "prompts"
    )

    for fname in sorted(os.listdir(prompt_dir)):
        if fname.endswith(".py") and not fname.startswith("__"):
            fpath = os.path.join(prompt_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            has_marker = "CACHE_BREAK" in content
            status = "[YES]" if has_marker else "[ NO]"
            print(f"    {status} {fname}")
            if has_marker:
                prompt_files_with_cache_break.append(fname)

    print(
        f"\n  {len(prompt_files_with_cache_break)} prompt files with CACHE_BREAK marker"
    )

    print("\n  [PASS] All unit tests passed!")


def test_cache_monitor():
    """Test the CacheMonitor class."""
    from app.utils.prompt_cache import PromptCacheMonitor

    print("\n" + "=" * 80)
    print("UNIT TESTS: Cache Monitor")
    print("=" * 80)

    monitor = PromptCacheMonitor()

    # Test 1: Empty stats
    stats = monitor.get_stats()
    assert stats["total_requests"] == 0
    print("  [PASS] Test 1: Empty stats")

    # Test 2: Record with mock response
    class MockUsage:
        prompt_tokens = 1000
        completion_tokens = 100
        prompt_tokens_details = None

    class MockResponse:
        usage = MockUsage()

    result = monitor.record(MockResponse(), model="test-model")
    assert result is not None
    assert result.cache_hit is False
    assert result.total_prompt_tokens == 1000
    print("  [PASS] Test 2: Record cache miss")

    # Test 3: Record with cached tokens
    class MockCachedDetails:
        cached_tokens = 800

    class MockCachedUsage:
        prompt_tokens = 1000
        completion_tokens = 100
        prompt_tokens_details = MockCachedDetails()

    class MockCachedResponse:
        usage = MockCachedUsage()

    result = monitor.record(MockCachedResponse(), model="test-model")
    assert result is not None
    assert result.cache_hit is True
    assert result.cached_tokens == 800
    assert result.cache_hit_rate == 80.0
    print("  [PASS] Test 3: Record cache hit")

    # Test 4: Aggregate stats
    stats = monitor.get_stats()
    assert stats["total_requests"] == 2
    assert stats["total_cached_tokens"] == 800
    assert stats["total_prompt_tokens"] == 2000
    print("  [PASS] Test 4: Aggregate stats correct")

    # Test 5: Reset
    monitor.reset()
    stats = monitor.get_stats()
    assert stats["total_requests"] == 0
    print("  [PASS] Test 5: Reset works")

    # Test 6: Summary string
    monitor.record(MockCachedResponse(), model="test")
    summary = monitor.get_summary()
    assert "Prompt Cache Summary" in summary
    print("  [PASS] Test 6: Summary generation")

    print("\n  [PASS] All cache monitor tests passed!")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("BotRunner Prompt Caching Test Suite")
    print("=" * 80)

    # Run unit tests first (no server needed)
    test_prompt_splitting()
    test_cache_monitor()

    # Run integration tests (server required)
    print("\n" + "=" * 80)
    print("INTEGRATION TESTS: Full Cache Validation")
    print("=" * 80)
    print(f"Target server: {BASE_URL}")
    print("Ensure server is running before proceeding.\n")

    try:
        report = asyncio.run(run_cache_tests())
        print_report(report)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback

        traceback.print_exc()
