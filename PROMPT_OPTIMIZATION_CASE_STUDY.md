# Case Study: Resolving Over-Refusal & Boundary Failures in RAG Pipelines

## 1. Executive Summary & Problem Formulation
In high-precision enterprise RAG pipelines, an overly broad refusal instruction often leads to **reflexive over-refusal on negative/boundary inference questions**. Specifically:
- When a user asks whether condition $X$ (e.g., latency exceeding a canary gate) causes outcome $Y$ (e.g., automatic rollback), a grounded LLM may correctly reason that $X$ and $Y$ are independent conditions, but then reflexively append: *"Therefore, I don't have enough information to answer that."*
- This causes automated LLM-as-a-judge harnesses to grade valid reasoning as a `REFUSED` failure.

---

## 2. Experimental Setup & Deterministic Calibration
To isolate model reasoning from stochastic generation noise:
1. **Pinned Temperature:** Set `temperature=0` using `google.genai.types.GenerateContentConfig(temperature=0)` across both generation and evaluation judge calls.
2. **Deterministic Stability Check:** Executed 3 back-to-back runs across adversarial multi-hop and near-miss test sets, confirming 100% reproducible verdicts across runs.
3. **Isolating Noise vs. Prompt Bugs:** Testing at `temperature=0` established that question **ADV-2** (Vault lease expiration + 30-day rotation schedule) had previously flipped due to default sampling noise (`temperature=0.7+`), achieving stable 3/3 `CORRECT` passes with no prompt changes needed. Only question **ADV-4** remained a genuine, deterministic over-refusal bug.

---

## 3. Exact Prompt Engineering Optimization

### Before (Naive Strict Grounding Prompt)
```python
PROMPT_TEMPLATE = """You answer questions using ONLY the context below.

Rules:
- If the context does not contain enough information to answer, say
  "I don't have enough information to answer that" — do not guess.
- Cite which source each fact comes from, like [source: filename].
- Do not use any knowledge outside the provided context.

Context:
{context}

Question: {question}

Answer:"""
```

### After (Boundary-Condition & Synthesis Aware Prompt)
```python
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
```

---

## 4. Prompt Diff Analysis

```diff
- Rules:
-- If the context does not contain enough information to answer, say
-  "I don't have enough information to answer that" — do not guess.
+- Rules:
 - Cite which source each fact comes from, like [source: filename].
 - Do not use any knowledge outside the provided context.
+- Synthesize facts across multiple provided sources when relevant.
+- Completely Unrelated Topics: If the context contains no relevant information about the asked topic, say:
+  "I don't have enough information to answer that"
+- Boundary & Stated Facts: When the context contains the relevant topics but does not state a specific causal link, rule, or outcome being asked about, state what the context does specify and clarify that the documents do not state or establish that relationship. (Do not tack on a generic refusal if you have already stated the document boundaries).
```

---

## 5. Key Failure Modes Solved

| Test ID | Test Category | Query | Failure Mode Before | Resolution After |
|:---|:---|:---|:---|:---|
| **ADV-4** | Near-Miss Distinction | *"During Phase 2 of a canary rollout, if p99 latency exceeds 120ms, does the system automatically roll back?"* | Model correctly analyzed gate vs. rollback, but appended trailing refusal (`REFUSED`). | Model clearly stated that 120ms is a gate condition while 5xx > 1% is the rollback trigger without trailing refusal (`CORRECT`). |
| **ADV-5** | Out-of-Domain Guard | *"What escalation path applies if NIS goes down in ap-southeast-1?"* | Verified no regression on unanswerables (`REFUSED`). | Remained strictly refused with zero hallucinations (`REFUSED`). |

---

## 6. Evaluation Harness Evolution: From Rigid Substring to Behavioral Grading

### The Problem
Initial evaluation harnesses often evaluate unanswerable queries using naive substring matching:
```python
# Fragile legacy check
if expected is None:
    return "REFUSED" if "don't have enough information" in actual.lower() else "INCORRECT"
```
When prompting was improved to explain boundary conditions (e.g., *"The documents define Vault lease errors and Patroni failover separately, but do not establish that one triggers the other"*), the system achieved **zero hallucinations**, but the rigid substring check flagged valid boundary explanations as `INCORRECT`.

### The Solution: Behavioral Refusal LLM Judge
```python
UNANSWERABLE_JUDGE_PROMPT = """The following question has no answer in the provided documents — any specific positive assertion or causal claim would be unsupported.

Question: {question}
Model's response: {actual}

Does the response correctly avoid asserting an unsupported claim (whether by an explicit refusal or by explaining that the documents do not state or establish the relationship)?

Respond with ONLY one word:
- "REFUSED" if it appropriately avoided asserting an unsupported claim (either through explicit refusal or by clearly stating the documents do not establish that relationship)
- "INCORRECT" if it confidently stated or hallucinated a claim not actually supported by the documents
"""
```

### Final Comprehensive Benchmark (32 Questions)
- **Answerable Questions:** 22 / 22 (100.0%)
- **Standard Out-of-Domain Unanswerables:** 7 / 7 (100.0%)
- **Adversarial Pseudo-Causal Traps:** 3 / 3 (100.0%)
- **Overall System Precision:** 32 / 32 (100.0%) with 0 Hallucinations.

