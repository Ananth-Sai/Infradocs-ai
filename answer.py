import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv
from index import search

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_POOL = [
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
]

PROMPT_TEMPLATE = """You answer questions using ONLY the facts in the context below.

Rules:
- Cite which source each fact comes from, like [source: filename].
- Do not use any knowledge outside the provided context.
- Synthesize facts across multiple provided sources when relevant.
- Completely Unrelated Topics: If the context contains no relevant information about the asked topic, say:
  "I don't have enough information to answer that"
- Boundary & Stated Facts: When the context contains the relevant topics but does not state a specific causal link, rule, or outcome being asked about, state what the context does specify and clarify that the documents do not state or establish that relationship. (Do not tack on a generic refusal if you have already stated the document boundaries).

Context:
{context}

Question: {question}

Answer:"""


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
    raise RuntimeError("All models and retries exhausted.")


def answer(question: str, top_k: int = 5) -> dict:
    results = search(question, top_k=top_k)
    context = "\n\n".join(
        f"[source: {r['source']}]\n{r['text']}" for r in results
    )
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    response_text = generate_with_fallback(prompt)
    return {
        "question": question,
        "answer": response_text,
        "sources_used": list({r["source"] for r in results}),
    }


if __name__ == "__main__":
    q = "What are the four default roles in InfraDocs Cloud Platform RBAC?"
    result = answer(q)
    print(f"Q: {result['question']}")
    print(f"A: {result['answer']}")
    print(f"Sources: {result['sources_used']}")
