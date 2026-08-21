"""
question_generator.py

Dynamically generates scenario-button question sets directly from whatever documents
are CURRENTLY indexed in the knowledge base, rather than relying on hardcoded lists.

Triggered explicitly by build_index(force_reindex=True) / document uploads / deletions
and saved to `generated_questions.json`.
"""

import os
import json
import random
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from index import collection, search

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_POOL = [
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
]

QUESTIONS_FILE = "generated_questions.json"

QUESTION_GEN_PROMPT = """You are generating example questions for a technical RAG system's
"Quick-Test Scenarios" buttons. Below are sample excerpts from the currently indexed knowledge base.

Generate natural, specific technical questions that a real engineer or user might ask.
Each question MUST be answerable using facts explicitly present in these excerpts — specific numbers,
thresholds, rules, roles, procedures, error codes, etc.

Do NOT write vague meta-questions like "summarize this document" or "what is this file about".
Do NOT invent facts not present in the excerpts.

Return exactly this JSON structure, nothing else, no markdown fences:
{{
  "overview": ["question 1", "question 2", "question 3"],
  "operations": ["question 1", "question 2", "question 3"],
  "edge_cases": ["question 1", "question 2"]
}}

"overview": high-level architecture, component roles, system purpose, or core concepts.
"operations": specific rules, numeric thresholds, operational procedures, or error handling.
"edge_cases": questions that require combining facts from two DIFFERENT excerpts below,
or a subtle boundary/near-miss distinction within an excerpt.

Excerpts:
{excerpts}
"""

REFUSAL_GEN_PROMPT = """Below are the source topics currently covered in a knowledge base:
{topic_summary}

Generate 3 candidate questions that sound plausible and professionally relevant to cloud infrastructure / engineering,
but ask about a SPECIFIC topic that is clearly NOT covered by any of the summaries above — something adjacent
but genuinely absent, so a grounded RAG system will correctly refuse to answer rather than guess.

Return ONLY a JSON list of 3 question strings, nothing else, no markdown fences:
["question 1", "question 2", "question 3"]
"""

FALLBACK_REFUSAL_QUESTION = "What is the corporate travel expense reimbursement limit for client dinners?"


def _call_gemini_json_with_fallback(prompt: str, max_retries: int = 4) -> dict | list:
    """Call Gemini with model rotation to safely parse JSON responses."""
    for attempt in range(max_retries):
        for model_name in MODEL_POOL:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json",
                    ),
                )
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                return json.loads(text.strip())
            except Exception as e:
                time.sleep(1)
                continue
    raise RuntimeError("Failed to generate questions across all available model endpoints.")


def _get_sample_chunks(max_chunks: int = 20) -> list[dict]:
    """Pull a representative sample across all indexed sources."""
    if collection.count() == 0:
        return []

    all_data = collection.get(include=["documents", "metadatas"])
    chunks = [
        {"text": doc, "source": meta.get("source", "unknown")}
        for doc, meta in zip(all_data["documents"], all_data["metadatas"])
    ]

    by_source: dict[str, list[dict]] = {}
    for c in chunks:
        by_source.setdefault(c["source"], []).append(c)

    per_source = max(1, max_chunks // max(1, len(by_source)))
    sample = []
    for source_chunks in by_source.values():
        sample.extend(random.sample(source_chunks, min(per_source, len(source_chunks))))

    return sample[:max_chunks]


def _generate_core_questions(sample_chunks: list[dict]) -> dict:
    excerpts = "\n\n".join(
        f"[source: {c['source']}]\n{c['text']}" for c in sample_chunks
    )
    prompt = QUESTION_GEN_PROMPT.format(excerpts=excerpts)
    try:
        return _call_gemini_json_with_fallback(prompt)
    except Exception:
        return {
            "overview": ["What are the primary components and roles described in the documentation?"],
            "operations": ["What operational procedures and threshold limits are enforced?"],
            "edge_cases": ["What conditions lead to service degradation or failover?"],
        }


def _generate_and_verify_refusal_question(sample_chunks: list[dict]) -> str:
    """Generates candidate refusal questions and verifies they do not match indexed documents."""
    sources = sorted({c["source"] for c in sample_chunks})
    topic_summary = "\n".join(f"- {s}" for s in sources)
    prompt = REFUSAL_GEN_PROMPT.format(topic_summary=topic_summary)

    try:
        candidates = _call_gemini_json_with_fallback(prompt)
        if isinstance(candidates, list):
            for candidate in candidates:
                results = search(str(candidate), top_k=1)
                if not results:
                    return str(candidate)
                # Cosine distance > 0.55 indicates no strong semantic match
                if results[0].get("distance", 1.0) > 0.55:
                    return str(candidate)
    except Exception:
        pass

    return FALLBACK_REFUSAL_QUESTION


def generate_and_save_questions() -> dict:
    """Main entry point: Generates questions from current index and persists to JSON."""
    sample = _get_sample_chunks()

    if not sample:
        result = {
            "overview": ["What is the primary purpose described in the documentation?"],
            "operations": ["What procedures or rules are defined in the documentation?"],
            "edge_cases": ["What boundary conditions apply to operations?"],
            "refusal": FALLBACK_REFUSAL_QUESTION,
        }
    else:
        core = _generate_core_questions(sample)
        refusal = _generate_and_verify_refusal_question(sample)
        result = {
            "overview": core.get("overview", []),
            "operations": core.get("operations", []),
            "edge_cases": core.get("edge_cases", []),
            "refusal": refusal,
        }

    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def load_questions() -> dict:
    """Loads the cached generated questions from disk."""
    if not os.path.exists(QUESTIONS_FILE):
        return generate_and_save_questions()
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return generate_and_save_questions()


if __name__ == "__main__":
    print("Generating dynamic test questions from current index...")
    res = generate_and_save_questions()
    print(json.dumps(res, indent=2))
