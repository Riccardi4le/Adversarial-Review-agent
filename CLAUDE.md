# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent
python main.py paper.pdf
python main.py https://arxiv.org/abs/2301.00001
python main.py paper.pdf -o report.md

# Required env var
GROQ_API_KEY=...   # copy .env.example → .env
```

## Architecture

**Pattern:** LangGraph `StateGraph` with a sequential check loop, mirroring the sibling `CG_agent` in `../CG_agent/`.

**State machine:**
```
START → ingest → classify → plan → check ──(pending?)──┐
                                              ↑          │
                                              └──────────┘
                                                         ↓
                                                      report → END
```

**Node responsibilities:**
- `ingest` — routes `paper_source` to `agent/pdf.py` (PDF local / PDF URL / HTML / plain text). ArXiv abstract URLs are auto-redirected to the PDF endpoint.
- `classify` — fast LLM call; sets `paper_type` which controls which checks are planned.
- `plan` — selects check list from `_CHECKS_BY_TYPE` dict in `nodes.py`, extracts top-5 claims via the fast model.
- `check` — runs one check per invocation, loops until `checks_completed == planned_checks`.
- `report` — aggregates `findings`, counts by severity, emits the final markdown report.

**Check types** (defined in `agent/llm.py`):
- `statistical` — enriched with a pure-Python pre-scan (`agent/grim.py`) before the LLM call: GRIM test on extracted mean/n pairs, p-value cluster analysis.
- `claim_support`, `citation`, `language`, `methodology` — LLM calls only.
- `language` check also runs a hardcoded tortured-phrase detector before the LLM call (see `_TORTURED` list in `llm.py`).

**LLM usage (Groq API):**
- `llama-3.1-8b-instant`: `classify_paper`, `extract_claims` (fast, cheap)
- `llama-3.3-70b-versatile`: all 5 check functions
- All calls share the same system prompt defined in `_SYSTEM` in `llm.py`.

**Key invariant:** each check function returns `list[Finding]` or `[]` — never raises. The `check_node` appends results to `state["findings"]` and adds the check type to `state["checks_completed"]`. Routing reads this to decide whether to loop.

**Failure handling:** API-layer failures may still happen. `check_node` catches them, records them in `state["errors"]`, marks the attempted check as completed, and lets the final report surface incomplete coverage instead of pretending the paper passed cleanly.

**Recent fixes:**
- GRIM validation now respects the displayed precision of the reported mean instead of using an overly loose tolerance.
- Groq API failures are surfaced into `state["errors"]` rather than silently becoming empty findings.
- The final recommendation distinguishes low-risk papers from incomplete or partially failed analysis.
- The web UI now sanitizes rendered markdown before inserting the final report into the DOM.

**Adding a new check type:**
1. Add a `_check_<name>` function in `agent/llm.py` returning `list[dict]`.
2. Register it in the `dispatch` dict in `run_check()`.
3. Add it to the appropriate lists in `_CHECKS_BY_TYPE` in `agent/nodes.py`.
No graph changes needed.
