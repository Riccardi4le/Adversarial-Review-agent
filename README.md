# Adversarial Reviewer Agent (ARV)

An AI agent that reviews academic papers like a hostile Nature/Science referee — finding p-hacking, unsupported claims, citation problems, language red flags, and methodology gaps.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) and the [Groq API](https://groq.com).

---

## What it does

Given a paper (PDF file, PDF URL, or arXiv link), the agent runs a structured adversarial review across five dimensions:

| Check | What it looks for |
|---|---|
| **Statistical** | P-hacking, GRIM failures, impossible means, implausible effect sizes |
| **Claim support** | Claims not backed by data, overstated conclusions, missing baselines |
| **Citation quality** | Self-citation clusters, circular references, outdated state-of-the-art |
| **Language** | Tortured phrases (paper mill indicator), excessive hedging, overclaiming |
| **Methodology** | Missing pre-registration, no data/code sharing, ethics, reproducibility |

Each finding is rated **critical / high / medium / low**, and the final report ends with a citation recommendation.

---

## Quick start

```bash
# 1. Clone and install
git clone https://github.com/<you>/Adversarial-Review-agent.git
cd Adversarial-Review-agent
pip install -r requirements.txt

# 2. Set your Groq API key
cp .env.example .env
# edit .env and add your key (get one at https://console.groq.com)

# 3a. Web UI (recommended)
python web_app.py
# open http://127.0.0.1:8000 in your browser

# 3b. CLI
python main.py https://arxiv.org/abs/2301.00001
python main.py paper.pdf
python main.py paper.pdf -o report.md
```

### Web UI

A local webapp is included (`web_app.py`) — no separate frontend build step required.

| Feature | Detail |
|---|---|
| **Input** | arXiv URL, any PDF/HTML URL, or drag-and-drop PDF upload |
| **Progress** | Live stepper showing each analysis phase |
| **Findings** | Cards stream in real-time as each check completes, colour-coded by severity |
| **Report** | Full markdown report rendered in-browser; one-click download as `.md` |

Built with FastAPI + Server-Sent Events. The CLI (`main.py`) is unchanged and still works independently.

---

## Requirements

- Python 3.10+
- A [Groq API key](https://console.groq.com)

Dependencies are in `requirements.txt`. No GPU or local model needed — everything runs via the Groq API.

Core dependencies: `langgraph`, `groq`, `pypdf`, `beautifulsoup4`, `rich` (CLI), `fastapi` + `uvicorn` + `python-multipart` (web UI).

---

## Recent fixes

The following reliability issues were fixed during review:

- **GRIM validation was too permissive.**
  Action taken: the statistical pre-scan now validates reported means against the precision actually shown in the paper, instead of accepting almost any nearby value.
- **LLM/API failures could be mistaken for "no issues found".**
  Action taken: Groq call failures are now surfaced and carried into the agent state, so failed checks no longer look like clean passes.
- **The final recommendation could look positive after partial failure.**
  Action taken: the report now distinguishes incomplete analysis and failed checks from genuinely low-risk papers.

Quick regression check:

```bash
python -c "from agent.grim import grim_test; print(grim_test('3.47',82), grim_test('3.48',82))"
```

Expected behavior: `3.47` with `n=82` is inconsistent, while `3.48` is accepted.

### Web UI fixes

The local web interface was also hardened:

- **Rendered markdown was too trusting.**
  Action taken: browser-side markdown rendering is now sanitized before insertion into the DOM.
- **Report output could inject raw HTML into the page.**
  Action taken: dangerous tags and attributes are stripped before showing the final report.

---

## Example output

```
┌─────────────────────────────────────────────┐
│ Adversarial Reviewer Agent                  │
│ Source: https://arxiv.org/abs/...           │
└─────────────────────────────────────────────┘
  ✓ ingested   The Effect of X on Y (2023)
  ✓ classified → empirical
  ✓ plan  5 claims · checks: statistical, claim_support, citation, language, methodology
  ✓ Statistical sanity — 3 finding(s) so far
  ✓ Claim support — 6 finding(s) so far
  ...

# Adversarial Report — The Effect of X on Y (2023)

## Summary
| Severity | Count |
|----------|-------|
| CRITICAL | 1     |
| HIGH     | 2     |
| MEDIUM   | 3     |
| LOW      | 1     |

HIGH-RISK **Recommendation:** Cite with caution. Significant issues detected.
```

---

## Architecture

```
START → ingest → classify → plan → check ──(pending?)──┐
                                           ↑            │
                                           └────────────┘
                                                        ↓
                                                     report → END
```

- `ingest` — extracts text from PDF / URL / plain text; auto-redirects arXiv abstract URLs to PDF
- `classify` — fast LLM call; identifies paper type (empirical, review, meta-analysis, theoretical)
- `plan` — selects the appropriate check list; extracts top-5 verifiable claims
- `check` — runs one check per loop iteration; loops until all checks complete
- `report` — aggregates findings by severity and renders the markdown report

**LLM usage:** `llama-3.1-8b-instant` for classify + claim extraction (fast/cheap); `llama-3.3-70b-versatile` for all five adversarial checks.

**Statistical pre-scan** (pure Python, no LLM): GRIM test on extracted mean/n pairs, p-value cluster analysis — results are injected into the statistical check prompt.

---

## Adding a new check type

1. Add a `_check_<name>` function in `agent/llm.py` returning `list[dict]`
2. Register it in the `dispatch` dict inside `run_check()`
3. Add it to the appropriate paper type lists in `_CHECKS_BY_TYPE` in `agent/nodes.py`

No graph changes needed.

---

## License

MIT
