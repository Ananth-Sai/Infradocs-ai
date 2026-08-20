# ⚡ InfraDocs AI — Cloud Infrastructure RAG Assistant

A high-precision, production-grade **Retrieval-Augmented Generation (RAG)** pipeline and interactive assistant built over enterprise cloud infrastructure and DevOps documentation.

This project demonstrates an end-to-end RAG architecture with **paragraph-aware chunking**, **hybrid retrieval (ChromaDB + BM25 Okapi + RRF)**, **deterministic LLM generation (`temperature=0`)**, and an **automated LLM-as-a-judge evaluation harness** achieving **100% accuracy with 0 hallucinations across a 32-question adversarial benchmark**.

---

## 🌟 Key Highlights & Engineering Breakthroughs

* 🛡️ **Zero Hallucinations (100% Grounded)**: Strict context grounding with enforced document-level citations (`[source: filename.md]`) and automated refusal guardrails on unindexed topics.
* 🔬 **Boundary-Condition Prompt Engineering**: Solved negative/boundary inference over-refusals (e.g., distinguishing gate conditions from rollback triggers) without weakening refusal safety. Detailed in [PROMPT_OPTIMIZATION_CASE_STUDY.md](PROMPT_OPTIMIZATION_CASE_STUDY.md).
* 🎯 **Deterministic & Reproducible Benchmarking**: Pinned `temperature=0` across generation and judge calls, isolating prompt logic from sampling noise.
* 🤖 **Behavioral LLM-as-a-Judge**: Upgraded the evaluation harness from fragile substring matching to behavioral refusal evaluation, accurately grading pseudo-causal boundary explanations.
* ⚡ **Hybrid Search & RRF**: Combines dense semantic embeddings (`all-MiniLM-L6-v2`) with sparse keyword indexing (BM25 Okapi) fused via Reciprocal Rank Fusion (RRF).
* 🎨 **Interactive Streamlit UI**: Dark-mode interface featuring real-time latency strips, knowledge base explorer, and quick-test scenario cyclers.

---

## 📊 Evaluation Scorecard & Empirical Proof

Tested against 4 versioned evaluation suites covering single-hop lookup, cross-document multi-hop synthesis, near-miss distinctions, and adversarial pseudo-causal traps:

| Benchmark Suite | Questions | Answerable Accuracy | Refusal Accuracy | Hallucination Rate | Source Precision |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Comprehensive Suite (`v2_full_benchmark.py`)** | **32** | **22 / 22 (100%)** | **10 / 10 (100%)** | **0 / 10 (0.0%)** | **100.0%** |
| **Edge-Case Suite (`v2_edge_cases.py`)** | **34** | **23 / 24 (95.8%)** | **10 / 10 (100%)** | **0 / 10 (0.0%)** | **100.0%** |
| **Adversarial Baseline (`adversarial_v1.py`)** | **5** | **4 / 4 (100%)** | **1 / 1 (100%)** | **0 / 1 (0.0%)** | **100.0%** |
| **Baseline Suite (`v1_baseline.py`)** | **24** | **18 / 18 (100%)** | **6 / 6 (100%)** | **0 / 6 (0.0%)** | **100.0%** |

*All raw execution outputs are preserved in [`eval_results/`](eval_results/).*

---

## 🏗️ Architecture Flow

```
                                  [ User / Benchmark Query ]
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. INGESTION (ingest.py)                                                                │
│ • Paragraph-aware text splitting (`\n\n`) preventing mid-sentence breaks                │
│ • Chunk sizing (~800 characters) + sliding overlap (~150 characters)                     │
│ • Generates structured chunk objects with source metadata & unique chunk IDs             │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. RETRIEVAL & INDEXING (index.py)                                                      │
│ • Dense Vector Store: ChromaDB persistent vector database (all-MiniLM-L6-v2, cosine)    │
│ • Sparse Keyword Index: BM25 Okapi for exact lexical token matching                     │
│ • Hybrid Fusion: Reciprocal Rank Fusion (RRF, k=60) combining vector + keyword hits      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. GROUNDED GENERATION (answer.py)                                                      │
│ • Pinned Determinism: `temperature=0` via GenerateContentConfig                         │
│ • Context Formatting: Strict grounding rules, multi-source synthesis & boundary checks  │
│ • Model Pool Fallback: Automated retry rotation across Gemini Flash models              │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       ▼                                             ▼
┌──────────────────────────────────────────────┐ ┌────────────────────────────────────────┐
│ 4. EVALUATION HARNESS (eval_harness.py)      │ │ 5. INTERACTIVE UI (app.py)             │
│ • Multi-Source List Matcher                  │ │ • Streamlit glassmorphic dark UI       │
│ • LLM-as-a-Judge for factual accuracy        │ │ • Strategy toggle (Dense vs. Hybrid)   │
│ • Behavioral Refusal Judge (detects correct  │ │ • Real-time latency & metrics strip    │
│   boundary statements vs. hallucinations)    │ │ • Knowledge Base Explorer              │
│ • Automated JSON logging to eval_results/    │ │ • Quick-test scenario randomizer       │
└──────────────────────────────────────────────┘ └────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
.
├── docs/                                    # Technical documentation corpus (Knowledge base)
│   ├── deployment_guide.md                  # Canary rollouts, traffic splitting & rollback triggers
│   ├── platform_overview.md                 # Architecture, NIS auth, RBAC roles & rate limits
│   └── troubleshooting_and_faq.md           # HTTP error codes, incident SLAs & Patroni failover
│
├── eval_sets/                               # Versioned benchmark datasets
│   ├── v1_baseline.py                       # 24-question locked baseline
│   ├── adversarial_v1.py                    # 5-question adversarial multi-hop / near-miss suite
│   ├── v2_full_benchmark.py                 # 32-question comprehensive suite (Official Benchmark)
│   └── v2_edge_cases.py                     # 34-question extended edge-case dataset
│
├── eval_results/                            # Stored JSON benchmark execution evidence
│   ├── eval_results_v2_full_benchmark.json  # 32/32 benchmark proof
│   ├── eval_results_v2_edge_cases.json      # 34-question edge-case proof
│   └── eval_results_adversarial_v1.json     # Adversarial suite proof
│
├── scripts/                                 # Diagnostic & variance measurement tools
│   ├── eval_adversarial_baseline.py         # Standalone diagnostic runner with distance logging
│   └── run_stability_test.py                # 3x repeat runner to measure temperature variance
│
├── .streamlit/                              # Streamlit configuration
│   └── config.toml                          # Dark theme & UI layout settings
│
├── ingest.py                                # Slice 1: Text extraction & paragraph-aware chunking
├── index.py                                 # Slice 2 & 5: ChromaDB vector indexing + BM25 & RRF
├── answer.py                                # Slice 3: Grounded Gemini generation (temp=0)
├── eval_harness.py                          # Slice 4: Automated evaluation runner
├── app.py                                   # Streamlit web application controller
├── ui_styles.py                             # CSS styling & citation badges
│
├── PROMPT_OPTIMIZATION_CASE_STUDY.md        # Technical case study on prompt & harness optimization
├── PROJECT_ARCHITECTURE_GUIDE.md            # Comprehensive system architecture & study guide
├── requirements.txt                         # Python dependencies
├── .env.example                             # Template environment variable configuration
└── README.md                                # Project documentation
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
* Python 3.10+
* A Google Gemini API Key ([Get one here](https://aistudio.google.com/apikey))

### 2. Setup Environment
```bash
# Clone the repository
git clone https://github.com/your-username/acme-rag-platform.git
cd acme-rag-platform

# Create and activate virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root directory (or copy `.env.example`):
```bash
cp .env.example .env
```
Add your Gemini API Key in `.env`:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Build Vector & BM25 Index
```bash
python -c "from index import build_index; build_index(force_reindex=True)"
```

---

## 💻 Running the Application & Benchmarks

### 🌐 Launch Interactive Web UI
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 🧪 Run the Comprehensive 32-Question Benchmark
```bash
python eval_harness.py v2_full_benchmark
```

### 🔬 Run the 3x Temperature Stability Test
```bash
python scripts/run_stability_test.py
```

---

## 📚 Deep-Dive Documentation

* 📄 **[PROMPT_OPTIMIZATION_CASE_STUDY.md](PROMPT_OPTIMIZATION_CASE_STUDY.md)**: A complete case study on diagnosing sampling noise (`temperature=0`), resolving boundary-condition false refusals, and evolving eval harnesses.
* 📄 **[PROJECT_ARCHITECTURE_GUIDE.md](PROJECT_ARCHITECTURE_GUIDE.md)**: In-depth technical cheat sheet and STAR interview preparation guide.

---

## 📄 License
MIT License. Free for educational and commercial use.
