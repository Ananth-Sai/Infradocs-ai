import streamlit as st
import time
from index import search, hybrid_search
from answer import generate_with_fallback, PROMPT_TEMPLATE
from ui_styles import (
    CUSTOM_CSS,
    format_citation_pills,
    get_doc_content,
    get_relevance_badge,
)

# --- Expanded Question Pools for Quick Scenarios (6-8 Questions Each) ---
RBAC_QUESTIONS = [
    "What are the four default roles in InfraDocs Cloud Platform RBAC?",
    "Which RBAC role has permission to manage IAM and service accounts?",
    "What operations are Viewer role users restricted from performing?",
    "What are the regional endpoints and data residency in eu-central-1 and us-east-1?",
    "How does InfraDocs Cloud Platform handle JWT session token validation and expiration?",
    "What is the maximum allowed replication lag between us-east-1 and eu-central-1?",
    "Which role is required to perform production canary promotions?",
]

CANARY_QUESTIONS = [
    "What are the requirements and duration for Phase 1 of canary deployment?",
    "What triggers an automatic rollback during canary deployment?",
    "What percentage of traffic is shifted during Phase 2 of canary rollout?",
    "How long does Phase 2 run before transitioning to Phase 3?",
    "How does InfraDocs Cloud Platform handle 504 Gateway Timeouts during canary rollout?",
    "What Prometheus error rate threshold causes a canary abort in Phase 1?",
    "What is the rollback procedure if node eviction occurs during deployment?",
]

REFUSAL_QUESTIONS = [
    "What is InfraDocs Cloud's policy on remote work and expense reimbursement?",
    "How do I set up office Bluetooth printer drivers on InfraDocs Cloud?",
    "What are the employee 401(k) retirement matching contributions?",
    "What time does the corporate cafeteria open on weekends?",
    "What is the company policy on bringing pets to the office?",
    "How do I request a company-issued mobile phone or SIM card?",
    "What is the annual gym wellness stipend amount for employees?",
]

# --- Page Setup & Theme ---
st.set_page_config(
    page_title="InfraDocs AI - Cloud Infrastructure RAG",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- Header ---
st.title("⚡ InfraDocs AI — Cloud Infrastructure RAG")
st.caption("High-precision Hybrid Retrieval (Dense Vector + BM25 Okapi + RRF) with Strict Grounded LLM Generation")



# --- Sidebar Configuration & Knowledge Explorer ---
with st.sidebar:
    st.header("⚙️ Search Engine Settings")
    retrieval_mode = st.radio(
        "Retrieval Strategy",
        options=["Hybrid (Dense + BM25 + RRF)", "Dense Only (ChromaDB)"],
        index=0,
        help="Hybrid fuses dense semantic vectors and sparse BM25 keywords with Reciprocal Rank Fusion.",
    )
    top_k = st.slider(
        "Retrieved Context Chunks (top_k)",
        min_value=1,
        max_value=8,
        value=5,
        step=1,
        help="Number of most relevant chunks passed to Gemini.",
    )

    st.markdown("---")
    st.subheader("📚 Knowledge Base Explorer")
    st.caption("Inspect indexed source files in real-time:")

    for filename, desc, icon in [
        ("deployment_guide.md", "Canary rollouts, traffic splitting, rollback triggers.", "📘"),
        ("platform_overview.md", "RBAC default roles, global infra, core architecture.", "⚙️"),
        ("troubleshooting_and_faq.md", "504 timeouts, node eviction, error resolution.", "❓"),
    ]:
        with st.expander(f"{icon} {filename}"):
            st.caption(desc)
            st.code(get_doc_content(filename), language="markdown")

    st.markdown("---")
    st.caption("⚡ **Vector Model**: `all-MiniLM-L6-v2` | **Engine**: `Gemini 3.5/3.7 Flash Pool`")

# --- State Management ---
if "question" not in st.session_state:
    st.session_state.question = ""
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "rbac_idx" not in st.session_state:
    st.session_state.rbac_idx = 0
if "canary_idx" not in st.session_state:
    st.session_state.canary_idx = 0
if "refusal_idx" not in st.session_state:
    st.session_state.refusal_idx = 0

def cycle_rbac():
    q = RBAC_QUESTIONS[st.session_state.rbac_idx % len(RBAC_QUESTIONS)]
    st.session_state.rbac_idx += 1
    st.session_state.question = q

def cycle_canary():
    q = CANARY_QUESTIONS[st.session_state.canary_idx % len(CANARY_QUESTIONS)]
    st.session_state.canary_idx += 1
    st.session_state.question = q

def cycle_refusal():
    q = REFUSAL_QUESTIONS[st.session_state.refusal_idx % len(REFUSAL_QUESTIONS)]
    st.session_state.refusal_idx += 1
    st.session_state.question = q

# --- Quick Test Prompt Chips with Dynamic Question Randomizer ---
st.markdown("##### 💡 Quick-Test Scenarios *(Click repeatedly to cycle questions)*:")
col_a, col_b, col_c = st.columns(3)
if col_a.button("🛡️ RBAC & Platform Arch (Cycle ↻)", use_container_width=True):
    cycle_rbac()
if col_b.button("🚀 Canary & Deployments (Cycle ↻)", use_container_width=True):
    cycle_canary()
if col_c.button("🚫 Refusal & Edge Cases (Cycle ↻)", use_container_width=True):
    cycle_refusal()

# --- Search Form ---
with st.form("search_form", clear_on_submit=False):
    input_query = st.text_input(
        "Ask a question about InfraDocs Cloud Platform:",
        value=st.session_state.question,
        placeholder="e.g., What are the automatic rollback triggers for canary deployment?",
    )
    submit_clicked = st.form_submit_button("⚡ Get Grounded Answer", type="primary")

# Execute search pipeline only on explicit user submit
if submit_clicked and input_query.strip():
    actual_question = input_query.strip()
    st.session_state.question = actual_question

    with st.status("🚀 Processing query through RAG pipeline...", expanded=True) as status:
        t0 = time.time()

        # Step 1: Retrieval
        status.write(f"🔎 **Step 1:** Retrieving top `{top_k}` chunks using `{retrieval_mode}`...")
        if "Hybrid" in retrieval_mode:
            retrieved_docs = hybrid_search(actual_question, top_k=top_k)
        else:
            retrieved_docs = search(actual_question, top_k=top_k)

        t_retrieval = (time.time() - t0) * 1000
        status.write(f"📄 Found **{len(retrieved_docs)} context chunks** in `{t_retrieval:.1f} ms`.")

        # Step 2: Generation
        t1 = time.time()
        status.write("🤖 **Step 2:** Formulating grounded context prompt & querying Gemini Flash...")
        context = "\n\n".join(
            f"[source: {r['source']}]\n{r['text']}" for r in retrieved_docs
        )
        prompt = PROMPT_TEMPLATE.format(context=context, question=actual_question)

        answer_text = generate_with_fallback(prompt)
        t_generation = time.time() - t1

        status.update(label="✅ Answer generated successfully!", state="complete", expanded=False)

        st.session_state.last_results = {
            "question": actual_question,
            "answer_text": answer_text,
            "retrieved_docs": retrieved_docs,
            "retrieval_mode": retrieval_mode,
            "top_k": top_k,
            "t_retrieval_ms": t_retrieval,
            "t_generation_s": t_generation,
        }

# --- Display Results ---
if st.session_state.last_results:
    res = st.session_state.last_results
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.subheader("💬 Grounded Answer")

        t_ret = res.get("t_retrieval_ms", 0.0)
        t_gen = res.get("t_generation_s", 0.0)
        mode_label = "Hybrid RRF" if "Hybrid" in res.get("retrieval_mode", "") else "Dense Vector"

        st.markdown(
            f"""
        <div class="metrics-strip">
            <div class="metric-pill">⏱️ Latency: <span>{t_ret:.0f}ms</span> ret / <span>{t_gen:.2f}s</span> llm</div>
            <div class="metric-pill">📊 Strategy: <span>{mode_label}</span> (top_{res.get('top_k', 5)})</div>
            <div class="metric-pill">🧠 Engine: <span>Gemini Flash Pool</span></div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        is_refusal = (
            "don't have enough information" in res["answer_text"].lower()
            or "not mentioned in the context" in res["answer_text"].lower()
        )
        badge_html = (
            '<div class="badge-refusal">⚠️ Out of Scope (Strict Refusal)</div>'
            if is_refusal
            else '<div class="badge-verified">🛡️ Verified & Grounded</div>'
        )

        formatted_answer = format_citation_pills(res["answer_text"])

        st.markdown(
            f"""
        <div class="glass-answer-card">
            {badge_html}
            <div>{formatted_answer}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.subheader("🔎 Retrieved Context Chunks")
        docs = res["retrieved_docs"]
        if not docs:
            st.info("No matching chunks found.")
        for i, doc in enumerate(docs, start=1):
            dist = doc.get("distance", 0.0)
            match_type = doc.get("match_type", "Dense Vector Match")
            rel_badge = get_relevance_badge(dist)
            strategy_badge = f'<span class="strategy-tag">{match_type}</span>'

            with st.expander(f"Chunk {i}: {doc['source']} ({match_type})", expanded=(i == 1)):
                st.markdown(
                    f"**Source:** `{doc['source']}` &nbsp;|&nbsp; {rel_badge} &nbsp;|&nbsp; {strategy_badge}",
                    unsafe_allow_html=True,
                )
                st.code(doc["text"], language="markdown")
