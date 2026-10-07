---
title: Adversarial Reviewer Agent
emoji: 🔬
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# Adversarial Reviewer Agent (ARV)

An AI agent that reviews academic papers like a hostile Nature/Science referee — finding p-hacking, unsupported claims, citation problems, language red flags, and methodology gaps.

Built with [LangGraph](https://github.com/langchain-ai/langgraph) and the [Groq API](https://groq.com).

**Live demo:** https://huggingface.co/spaces/Riccardi4le/ARV_agent

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

The methodology check is field-aware: pre-registration and ethics approval are **not** flagged for CS/ML/systems papers, only for confirmatory clinical or behavioural studies.

---

## Quick start

### Hugging Face Space (no install)

Just open the live demo and paste an arXiv URL or upload a PDF:
👉 https://huggingface.co/spaces/Riccardi4le/ARV_agent

### Local

```bash
# 1. Clone and install
git clone https://github.com/Riccardi4le/Adversarial-Review-agent.git
cd Adversarial-Review-agent
pip install -r requirements.txt

# 2. Set your Groq API key
cp .env.example .env
# edit .env and add your key (get one at https://console.groq.com)

# 3a. Web UI (recommended)
python web_app.py
# open http://127.0.0.1:7860 in your browser

# 3b. CLI
python main.py https://arxiv.org/abs/2301.00001
python main.py paper.pdf
python main.py paper.pdf -o report.md
```

### Docker

```bash
docker build -t arv-agent .
docker run -p 7860:7860 -e GROQ_API_KEY=$GROQ_API_KEY arv-agent
```

---

## Web UI

A local webapp is included (`web_app.py`) — no separate frontend build step required.

| Feature | Detail |
|---|---|
| **Input** | arXiv URL, any PDF/HTML URL, or drag-and-drop PDF upload |
| **Progress** | Live stepper showing each analysis phase |
| **Findings** | Cards stream in real-time as each check completes, colour-coded by severity |
| **Report** | Full markdown report rendered in-browser; one-click download as `.md` |

Built with FastAPI + Server-Sent Events. The CLI (`main.py`) is unchanged and still works independently.

---

## Architecture

LangGraph state machine with sequential nodes:

```
ingest → classify → plan → [statistical | claim_support | citation | language | methodology] → report
```

- **`agent/graph.py`** — graph wiring
- **`agent/nodes.py`** — node implementations
- **`agent/llm.py`** — Groq prompts (GPT-OSS 20B for extraction, GPT-OSS 120B for adversarial checks)
- **`agent/grim.py`** — GRIM arithmetic validator (deterministic pre-scan)
- **`agent/pdf.py`** — PDF / HTML / arXiv ingestion
- **`agent/state.py`** — shared `AgentState` typed dict

---

## Deployment

The repo includes a `Dockerfile` and the HF Spaces frontmatter at the top of this README, so deploying to Hugging Face Spaces is just:

```bash
git remote add hf https://huggingface.co/spaces/<user>/<space-name>
git push hf main
```

Set `GROQ_API_KEY` as a secret in the Space settings.

---

## Requirements

- Python 3.10+
- A [Groq API key](https://console.groq.com)

Dependencies are in `requirements.txt`. No GPU or local model needed — everything runs via the Groq API.

Core dependencies: `langgraph`, `groq`, `pypdf`, `beautifulsoup4`, `rich` (CLI), `fastapi` + `uvicorn` + `python-multipart` (web UI).

---

## Reliability notes

- **GRIM validation** matches the precision actually shown in the paper rather than accepting any nearby value.
- **LLM/API failures** are surfaced into the agent state, so failed checks are not silently mistaken for "no issues found".
- **The final recommendation** distinguishes incomplete analysis and failed checks from genuinely low-risk papers.
- **Markdown rendering** in the web UI is sanitised before DOM insertion.

Quick regression check:

```bash
python -c "from agent.grim import grim_test; print(grim_test('3.47',82), grim_test('3.48',82))"
```

Expected: `3.47` with `n=82` is inconsistent, `3.48` is accepted.
