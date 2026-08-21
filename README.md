# ⚡ InfraDocs AI — Cloud Infrastructure RAG Assistant

A Retrieval-Augmented Generation system built over technical documentation, with a strong emphasis on **measuring and proving** it actually works — not just building a demo that looks like it does.

Given a question, the system retrieves relevant chunks from a local knowledge base, generates a grounded answer with source citations, and explicitly refuses to answer when the docs don't contain enough information. Every claim about its accuracy is backed by an automated, versioned evaluation suite — including deliberately adversarial questions designed to catch hallucination and multi-hop reasoning failures.

---

## Why this project exists

Most "I built a RAG app" projects stop at a working demo. This one goes further: it includes a full diagnostic loop where a real bug was found (the model was over-refusing on boundary-condition questions), correctly isolated from sampling noise (using `temperature=0` to rule out randomness before touching the prompt), fixed with a targeted prompt change, and verified with a before/after benchmark — including confirming the fix didn't cause any regressions elsewhere.

The full writeup of that process is in [`PROMPT_OPTIMIZATION_CASE_STUDY.md`](PROMPT_OPTIMIZATION_CASE_STUDY.md).

---

## 📊 Results

Final verified benchmark, `eval_sets/v2_full_benchmark.py` (32 questions), `temperature=0`, dense-only retrieval (`search()` in `index.py` — the hybrid BM25+RRF path exists but is not the default and hasn't been benchmarked against this baseline yet):

| Benchmark Suite | Questions | Answerable Accuracy | Refusal Accuracy | Hallucination Rate | Source Precision |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Comprehensive Suite (`v2_full_benchmark.py`)** | **32** | **22 / 22 (100%)** | **10 / 10 (100%)** | **0 / 10 (0.0%)** | **100.0%** |
| **Edge-Case Suite (`v2_edge_cases.py`)** | **34** | **23 / 24 (95.8%)** | **10 / 10 (100%)** | **0 / 10 (0.0%)** | **100.0%** |
| **Adversarial Baseline (`adversarial_v1.py`)** | **5** | **4 / 4 (100%)** | **1 / 1 (100%)** | **0 / 1 (0.0%)** | **100.0%** |
| **Baseline Suite (`v1_baseline.py`)** | **24** | **18 / 18 (100%)** | **6 / 6 (100%)** | **0 / 6 (0.0%)** | **100.0%** |

This includes single-hop questions, multi-hop questions requiring synthesis across two documents, near-miss questions designed to test whether the model conflates two similar-but-distinct facts, and adversarial pseudo-causal traps designed to bait a false causal claim.

**Known miss**: The one edge-case failure (23/24) was *"Which service assigns principals to the four default RBAC roles in ACP?"* — the model refused instead of answering, even though the docs separately state that the Nexus Identity Service (NIS) handles authentication and list the four roles (Viewer, Operator, SecurityAdmin, SuperAdmin). The docs do not explicitly state that NIS is the service that assigns principals to those roles, so this reads as a genuine multi-hop synthesis gap — the same category of bug documented in the [case study](PROMPT_OPTIMIZATION_CASE_STUDY.md), just not yet chased down and fixed. Left in deliberately rather than removed from the suite, since a benchmark that only contains fixed bugs isn't proving much.

*All raw execution outputs are preserved in [`eval_results/`](eval_results/).*

---

## 🏗️ Architecture

```
[User Question]
       │
       ▼
[ingest.py]   — Loads docs/*.md, .txt, .pdf, .docx, .csv, .json, .html;
                 splits into paragraph-aware chunks with overlap
       │
       ▼
[index.py]    — Embeds chunks locally (sentence-transformers, all-MiniLM-L6-v2),
                 stores in a persistent ChromaDB vector store;
                 BM25 Okapi sparse index + Reciprocal Rank Fusion (RRF)
       │
       ▼
[answer.py]   — Retrieves top-k relevant chunks, generates a grounded answer via
                 Gemini (temperature=0), with mandatory source citations and a
                 boundary-aware refusal policy; model pool fallback on rate limits
       │
       ▼
[eval_harness.py] — Runs versioned question sets against the pipeline, scores
                     correctness and refusal behavior with an LLM-as-judge,
                     outputs a benchmark report
```

A Streamlit UI (`app.py`) sits on top for interactive querying, with a source inspector, retrieval settings, and document management.

---

## 📁 Project Structure

```
.
├── docs/                              # Knowledge base (swappable — any docs work)
├── eval_sets/                         # Versioned, immutable question sets
│   ├── v1_baseline.py                 # 24-question core baseline
│   ├── adversarial_v1.py              # 5-question multi-hop / near-miss set
│   ├── v2_full_benchmark.py           # 32-question comprehensive suite
│   └── v2_edge_cases.py              # Extended edge cases
├── eval_results/                      # Raw JSON output from each benchmark run
├── scripts/                           # Diagnostic tooling
│   ├── eval_adversarial_baseline.py
│   └── run_stability_test.py          # Multi-run variance check
│
├── ingest.py                          # Text extraction & paragraph-aware chunking
├── index.py                           # Embedding + vector store (dense + hybrid search)
├── answer.py                          # Grounded generation (temp=0, model pool fallback)
├── eval_harness.py                    # Automated benchmark runner
├── question_generator.py              # Dynamic quick-test scenario generator from indexed docs
├── app.py                             # Streamlit web application
├── ui_styles.py                       # CSS design system & citation badges
│
├── .streamlit/config.toml             # Dark theme & UI layout settings
├── PROMPT_OPTIMIZATION_CASE_STUDY.md  # The diagnostic story: bug found, isolated, fixed, verified
├── requirements.txt                   # Python dependencies
├── .env.example                       # Template environment variable configuration
└── README.md
```

---

## 🚀 Setup

### Prerequisites
* Python 3.10+
* A Google Gemini API Key ([Get one here](https://aistudio.google.com/apikey))

### Install & Configure
```bash
# Clone the repository
git clone https://github.com/your-username/infradocs-ai.git
cd infradocs-ai

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Then add your GEMINI_API_KEY in .env
```

Get a free Gemini API key at https://aistudio.google.com/apikey.

---

## 💻 Usage

```bash
# 1. Build the vector index from docs/
python -c "from index import build_index; build_index(force_reindex=True)"

# 2. Launch the interactive UI
streamlit run app.py

# 3. Run the full 32-question evaluation benchmark
python eval_harness.py v2_full_benchmark

# 4. Run the 3x temperature stability test
python scripts/run_stability_test.py
```

---

## 🔑 Key Design Decisions

- **Local embeddings, hosted generation.** Embeddings run locally via `sentence-transformers` (free, no API quota consumed on indexing). Only the generation step calls the Gemini API.
- **`temperature=0` throughout.** Both generation and the LLM-as-judge evaluation calls are pinned to zero temperature, so benchmark results are reproducible rather than a snapshot of one random sample.
- **Boundary-aware refusal, not blanket refusal.** The model distinguishes between "no relevant information exists" (refuse) and "relevant facts exist but don't establish the specific relationship being asked about" (state what's known and name the gap). This was the exact bug found and fixed — see the [case study](PROMPT_OPTIMIZATION_CASE_STUDY.md).
- **Behavioral evaluation, not string matching.** The eval harness grades unanswerable questions by asking a judge model whether the response appropriately avoided an unsupported claim, rather than checking for one exact refusal phrase.
- **Dense retrieval by default; hybrid available.** The core pipeline and benchmarked results use local `sentence-transformers` embeddings (`search()` in `index.py`). A hybrid BM25 + dense RRF implementation (`hybrid_search()`) is built and toggleable in the Streamlit UI, but has not yet been benchmarked against the dense baseline.
- **Corpus-adaptive quick-test questions.** Rather than hardcoding demo questions tied to one specific doc set, `question_generator.py` samples chunks from the active vector index upon rebuilds to automatically generate realistic overview, operational, and edge-case questions, with vector-verified unanswerable refusal candidates saved to `generated_questions.json`.

---

## ⚠️ System Boundaries & Known Limits

While the system achieves **0% hallucination rate** across our adversarial benchmarks, the following operational boundaries apply:

* **Document integrity ("Garbage in, garbage out")**: The model reflects the ground truth of files in `docs/`. If source documentation contains outdated information, the AI will cite those exact document states without guessing corrections.
* **Retrieval depth (`top_k`)**: If answering a broad query requires synthesizing facts scattered across more chunks than the configured `top_k`, some context may be omitted unless increased in the UI sidebar.
* **Scanned / image-only PDFs**: PDFs must contain selectable text. Scanned bitmap images without embedded OCR text require pre-processing before ingestion.
* **Out-of-corpus refusal**: Queries on topics absent from the knowledge base trigger explicit safety refusals rather than speculative answers.

---

## 📚 Documentation

* [`PROMPT_OPTIMIZATION_CASE_STUDY.md`](PROMPT_OPTIMIZATION_CASE_STUDY.md) — The diagnostic story: bug found, isolated from sampling noise, fixed with a targeted prompt change, verified with before/after benchmarks.

---

## 📄 License

MIT License. Free for educational and commercial use.
