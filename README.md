<div align="center">

# ⚡ InfraDocs AI — Cloud Infrastructure RAG Assistant

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Gemini API](https://img.shields.io/badge/Google-Gemini%203.x-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-FF6B6B?style=for-the-badge)](https://www.trychroma.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-9945FF?style=for-the-badge)](./LICENSE)

<p align="center">
  A Retrieval-Augmented Generation system built with a strong emphasis on <b>measuring and proving</b><br/>
  it actually works — not just building a demo that looks like it does.
</p>

</div>

---

## Why this project exists

Most "I built a RAG app" projects stop at a working demo. This one includes a full diagnostic loop: a real bug was found (the model was over-refusing on boundary-condition questions), correctly isolated from sampling noise using `temperature=0` before touching the prompt, fixed with a targeted change, and verified with a before/after benchmark — including confirming the fix caused no regressions elsewhere.

The full writeup is in [`PROMPT_OPTIMIZATION_CASE_STUDY.md`](PROMPT_OPTIMIZATION_CASE_STUDY.md).

## Results

Recomputed directly from the raw JSON in [`eval_results/`](eval_results/), not just quoted — `temperature=0`, **dense-only retrieval** (the hybrid BM25+RRF path exists but isn't the default and hasn't been benchmarked against this baseline yet):

| Benchmark Suite | Questions | Answerable Accuracy | Refusal Accuracy | Hallucination Rate |
|:---|:---:|:---:|:---:|:---:|
| **Comprehensive Suite** | 32 | 21/22 (95.5%) | 10/10 (100%) | 0/10 (0.0%) |
| **Edge-Case Suite** | 34 | 23/24 (95.8%) | 10/10 (100%) | 0/10 (0.0%) |
| **Adversarial Baseline** | 5 | 4/4 (100%) | 1/1 (100%) | 0/1 (0.0%) |

**Known miss #1 (judge-calibration, not a model failure):** the Vault-lease/rotation-schedule question was marked `INCORRECT` even though the model's actual answer correctly states the error code, the HTTP status, and the rotation window — then correctly declines to assert a causal link the docs don't establish, which is exactly the boundary-aware behavior this project is built around. The strict `expected_answer` template likely didn't account for that phrasing. Since the pipeline uses a model-pool fallback, different runs may hit different underlying models even at `temperature=0`, so exact wording (and a strict judge's verdict on it) isn't fully deterministic run-to-run. Left in as an honest, unresolved finding rather than quietly re-scored.

**Known miss #2 (genuine multi-hop gap):** *"Which service assigns principals to the four default RBAC roles in ACP?"* — the model refused instead of answering, even though the docs separately state that the Nexus Identity Service (NIS) handles authentication and list the four roles. The docs don't explicitly state NIS assigns principals to those roles, so this is a real synthesis gap, not fixed yet. Left in deliberately — a benchmark that only contains fixed bugs isn't proving much.

## Architecture

```
[User Question]
       │
       ▼
[ingest.py]    — Loads docs (.md/.txt/.pdf/.docx/.csv/.json/.html), paragraph-aware chunking
       │
       ▼
[index.py]     — Local embeddings (sentence-transformers), ChromaDB vector store,
                  BM25 + RRF hybrid path (built, not yet benchmarked)
       │
       ▼
[answer.py]    — Grounded generation via Gemini (temperature=0), mandatory citations,
                  boundary-aware refusal policy, model-pool fallback on rate limits
       │
       ▼
[eval_harness.py] — Versioned benchmark suites, LLM-as-judge behavioral scoring
       │
       ▼
[question_generator.py] — Regenerates quick-test questions from whatever's currently
                            indexed, whenever docs are uploaded, deleted, or reindexed
```

A Streamlit UI (`app.py`) provides interactive querying with a source inspector and document management.

## Key Design Decisions

- **Local embeddings, hosted generation** — no API quota consumed on indexing, only on answer generation.
- **`temperature=0` throughout** — reproducible generation, though see "Known miss #1" above for a real limitation this doesn't fully solve when a model-pool fallback is involved.
- **Boundary-aware refusal** — distinguishes "no relevant information exists" from "relevant facts exist but don't establish the specific relationship asked about."
- **Behavioral evaluation, not string matching** — the judge assesses whether a claim was appropriately avoided, not whether one exact phrase appears.
- **Dynamic quick-test questions** — `question_generator.py` samples the currently indexed corpus and regenerates fact-specific test questions (including a verified out-of-scope refusal test) on every reindex, so the demo never goes stale against swapped-in documents.

## Tech Stack

Python · Streamlit · ChromaDB · sentence-transformers (`all-MiniLM-L6-v2`) · Google Gemini API (3.5/3.6/3.7-flash pool with fallback) · rank-bm25

## Getting Started

```bash
git clone https://github.com/Ananth-Sai/Infradocs-ai.git
cd Infradocs-ai
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
cp .env.example .env  # add your GEMINI_API_KEY
```

```bash
# Build the index
python -c "from index import build_index; build_index(force_reindex=True)"

# Launch the UI
streamlit run app.py

# Run the full benchmark
python eval_harness.py v2_full_benchmark
```

## Documentation

- [`PROMPT_OPTIMIZATION_CASE_STUDY.md`](PROMPT_OPTIMIZATION_CASE_STUDY.md) — the diagnostic story, prompt diffs, before/after benchmarks

## License

MIT
