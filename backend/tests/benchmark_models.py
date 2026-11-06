"""
backend/tests/benchmark_models.py
Benchmark suite for evaluating local AI models (Qwen vs Nemotron) on Ollama.
Tests structured JSON generation, instruction following, generation latency, and token throughput.
"""

import os
import sys
import time
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import django
from django.conf import settings
if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

from sitemap_app.providers import OllamaProvider, CompletionRequest


def benchmark_model(model_name: str) -> dict:
    print(f"\n=======================================================")
    print(f"BENCHMARKING MODEL: {model_name}")
    print(f"=======================================================")

    provider = OllamaProvider(model=model_name, timeout=60)
    if not provider.is_available():
        print(f"ERROR: Ollama server is not reachable at {provider.base_url}")
        return {"error": "Ollama unreachable"}

    results = {
        "model": model_name,
        "json_test": {},
        "instruction_following_test": {},
        "wireframe_generation_test": {}
    }

    # -------------------------------------------------------------
    # Test 1: Structured JSON Generation
    # -------------------------------------------------------------
    print("\n--- Test 1: Structured JSON Generation ---")
    json_prompt = (
        "Generate a sitemap for an artisan bakery website named 'Golden Crust'. "
        "Return a JSON object with keys: website_name (string), navigation (array of strings), "
        "and pages (array of objects with 'name', 'path', and 'sections')."
    )
    req1 = CompletionRequest(
        prompt=json_prompt,
        system_instruction="You are a strict JSON generator. Output only valid JSON without explanation.",
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=600
    )

    t0 = time.time()
    resp1 = provider.complete(req1)
    duration1 = time.time() - t0

    parsed1 = resp1.parse_as_json()
    valid_json1 = parsed1 is not None and isinstance(parsed1, dict)
    has_keys = False
    if valid_json1:
        has_keys = all(k in parsed1 for k in ['website_name', 'navigation', 'pages'])

    tps1 = resp1.usage.completion_tokens / (duration1 if duration1 > 0 else 1)

    print(f"Success: {resp1.success}")
    print(f"Valid JSON Parsed: {valid_json1}")
    print(f"Required Schema Keys Present: {has_keys}")
    print(f"Duration: {duration1:.2f}s")
    print(f"Tokens: {resp1.usage.completion_tokens} ({tps1:.1f} tokens/sec)")

    results["json_test"] = {
        "success": resp1.success,
        "valid_json": valid_json1,
        "schema_complete": has_keys,
        "duration_sec": round(duration1, 2),
        "completion_tokens": resp1.usage.completion_tokens,
        "tokens_per_sec": round(tps1, 1)
    }

    # -------------------------------------------------------------
    # Test 2: Instruction-Following & Negative Constraint Adherence
    # -------------------------------------------------------------
    print("\n--- Test 2: Instruction Following & Negative Constraints ---")
    instruction_prompt = (
        "List exactly 4 key benefits of our cloud hosting service for developers. "
        "Strict rules:\n"
        "1. Return ONLY a JSON array of strings.\n"
        "2. Exactly 4 items, no more, no less.\n"
        "3. Each string must be under 15 words.\n"
        "4. Do NOT include markdown code fences or conversational text."
    )
    req2 = CompletionRequest(
        prompt=instruction_prompt,
        system_instruction="Follow constraints strictly. Output JSON array only.",
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=300
    )

    t0 = time.time()
    resp2 = provider.complete(req2)
    duration2 = time.time() - t0

    parsed2 = resp2.parse_as_json()
    if isinstance(parsed2, dict):
        # Extract the list if wrapped in an object like {"strings": [...]}
        for v in parsed2.values():
            if isinstance(v, list):
                parsed2 = v
                break
    is_list = isinstance(parsed2, list)
    exact_count = is_list and len(parsed2) == 4
    no_markdown_in_raw = "```" not in resp2.content

    print(f"Valid List: {is_list}")
    print(f"Exact 4 Items: {exact_count}")
    print(f"Clean Output (No Fences in Raw): {no_markdown_in_raw}")
    print(f"Duration: {duration2:.2f}s")

    results["instruction_following_test"] = {
        "success": resp2.success,
        "valid_array": is_list,
        "exact_count_matched": exact_count,
        "no_markdown_fences": no_markdown_in_raw,
        "duration_sec": round(duration2, 2)
    }

    # -------------------------------------------------------------
    # Test 3: Wireframe Page Section Generation
    # -------------------------------------------------------------
    print("\n--- Test 3: Wireframe Page Section Generation ---")
    wf_prompt = (
        "Generate a structured wireframe layout for the 'Home' page of an AI SaaS platform. "
        "Return a JSON array of section objects. Each object must have: "
        "'type' (one of: navbar, hero, features, testimonials, footer), "
        "'title' (string), 'description' (string), and 'layoutVariant' (string)."
    )
    req3 = CompletionRequest(
        prompt=wf_prompt,
        system_instruction="You are a professional UX architect. Return a JSON array.",
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=800
    )

    t0 = time.time()
    resp3 = provider.complete(req3)
    duration3 = time.time() - t0

    parsed3 = resp3.parse_as_json()
    if isinstance(parsed3, dict) and "sections" in parsed3:
        parsed3 = parsed3["sections"]
    elif isinstance(parsed3, dict):
        for v in parsed3.values():
            if isinstance(v, list):
                parsed3 = v
                break
    valid_sections = isinstance(parsed3, list) and len(parsed3) >= 3
    section_types = [s.get('type') for s in parsed3 if isinstance(s, dict)] if isinstance(parsed3, list) else []

    print(f"Sections Generated: {len(section_types)}")
    print(f"Types: {section_types}")
    print(f"Duration: {duration3:.2f}s")

    results["wireframe_generation_test"] = {
        "success": resp3.success,
        "section_count": len(section_types),
        "section_types": section_types,
        "duration_sec": round(duration3, 2)
    }

    return results


if __name__ == "__main__":
    target_models = ["qwen2.5:3b"]
    if len(sys.argv) > 1:
        target_models = sys.argv[1:]

    all_results = {}
    for m in target_models:
        all_results[m] = benchmark_model(m)

    out_file = backend_dir / "benchmark_results.json"
    with open(out_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nAll benchmark results saved to: {out_file}")
