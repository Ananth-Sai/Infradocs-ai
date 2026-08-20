import os
import sys
import json
import time
import importlib
from google import genai
from google.genai import types
from dotenv import load_dotenv
from answer import answer

# Load eval set by version: python eval_harness.py v2_edge_cases
eval_version = sys.argv[1] if len(sys.argv) > 1 else "v1_baseline"
try:
    eval_module = importlib.import_module(f"eval_sets.{eval_version}")
    EVAL_SET = getattr(eval_module, "EVAL_SET", None) or getattr(eval_module, "ADVERSARIAL_SET")
except (ImportError, AttributeError):
    print(f"Error: eval_sets/{eval_version}.py not found or has no EVAL_SET/ADVERSARIAL_SET")
    sys.exit(1)

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_POOL = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]

JUDGE_PROMPT = """You are grading an AI's answer against the expected answer.

Question: {question}
Expected answer: {expected}
AI's actual answer: {actual}

Respond with ONLY one word:
- "CORRECT" if the AI's answer matches the expected answer's meaning
- "INCORRECT" if it's wrong, misses the key facts, or contradicts the expected answer
- "REFUSED" if the AI explicitly stated it doesn't have enough information
"""

UNANSWERABLE_JUDGE_PROMPT = """The following question has no answer in the provided documents — any specific positive assertion or causal claim would be unsupported.

Question: {question}
Model's response: {actual}

Does the response correctly avoid asserting an unsupported claim (whether by an explicit refusal or by explaining that the documents do not state or establish the relationship)?

Respond with ONLY one word:
- "REFUSED" if it appropriately avoided asserting an unsupported claim (either through explicit refusal or by clearly stating the documents do not establish that relationship)
- "INCORRECT" if it confidently stated or hallucinated a claim not actually supported by the documents
"""

def generate_with_fallback(prompt: str, max_retries: int = 5) -> str:
    for attempt in range(max_retries):
        for model_name in MODEL_POOL:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0),
                )
                return response.text
            except Exception as e:
                time.sleep(5)
                continue
    raise RuntimeError("All judge models and retries exhausted.")

def judge(question: str, expected: str | None, actual: str) -> str:
    if expected is None:
        prompt = UNANSWERABLE_JUDGE_PROMPT.format(question=question, actual=actual)
    else:
        prompt = JUDGE_PROMPT.format(question=question, expected=expected, actual=actual)
    
    verdict = generate_with_fallback(prompt)
    return verdict.strip().upper()

def run_eval():
    # Evaluates the complete dataset
    eval_subset = EVAL_SET
    results = []
    correct = 0
    hallucinations = 0
    correctly_refused = 0

    print(f"Running evaluation against all {len(eval_subset)} test cases...\n")

    for i, item in enumerate(eval_subset, start=1):
        print(f"[{i}/{len(eval_subset)}] Evaluating: {item['question']}")
        r = answer(item["question"])
        verdict = judge(item["question"], item["expected_answer"], r["answer"])
        time.sleep(2)  # Keeps RPM safely within free-tier rate limits
        
        expected_src = item["expected_source"]
        is_source_correct = (
            expected_src is None
            or (isinstance(expected_src, list) and all(s in r["sources_used"] for s in expected_src))
            or (isinstance(expected_src, str) and expected_src in r["sources_used"])
        )

        results.append({
            "question": item["question"],
            "answerable": item["answerable"],
            "actual_answer": r["answer"],
            "expected_answer": item["expected_answer"],
            "verdict": verdict,
            "source_correct": is_source_correct,
            "sources_used": r["sources_used"],
        })

        if item["answerable"] and verdict == "CORRECT":
            correct += 1
        if not item["answerable"] and verdict == "INCORRECT":
            hallucinations += 1
        if not item["answerable"] and verdict == "REFUSED":
            correctly_refused += 1

    total = len(eval_subset)
    answerable_count = sum(1 for i in eval_subset if i["answerable"])
    unanswerable_count = total - answerable_count

    answerable_results = [r for r in results if r["answerable"]]
    source_precision = (
        sum(1 for r in answerable_results if r["source_correct"]) / len(answerable_results)
        if answerable_results else 0.0
    )

    print("\n" + "=" * 40)
    print(f"    RAG BENCHMARK REPORT ({eval_version})")
    print("=" * 40)
    print(f"Total questions evaluated: {total}")
    print(f"Correct answers:           {correct}/{answerable_count}")
    print(f"Correctly refused:         {correctly_refused}/{unanswerable_count}")
    print(f"Hallucinations (unans Qs): {hallucinations}/{unanswerable_count}")
    print(f"Retrieval source precision:{source_precision:.2%}")
    print("=" * 40)

    os.makedirs("eval_results", exist_ok=True)
    output_file = os.path.join("eval_results", f"eval_results_{eval_version}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to {output_file}")

if __name__ == "__main__":
    run_eval()