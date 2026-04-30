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

Attacks an academic paper like a hostile Nature reviewer: p-hacking detection,
claim support verification, citation quality, language red flags (tortured
phrases, AI-paraphrased terminology), and methodology audit.

Built with **LangGraph** + **Groq** (Llama 3.1 8B for extraction, Llama 3.3 70B
for adversarial checks). FastAPI backend with Server-Sent Events for live
progress streaming.

## Usage

Paste an arXiv URL or upload a PDF. The agent ingests the paper, classifies it,
plans the relevant checks, runs them in sequence, and produces a structured
Markdown report with severity-tagged findings.

## Local run

```bash
pip install -r requirements.txt
export GROQ_API_KEY=...
python web_app.py
```

CLI variant:

```bash
python main.py paper.pdf -o report.md
```
