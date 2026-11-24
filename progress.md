# My Learning Progress — Zero to Hero AI Agent

Started: 2026-05-13

---

## How to Use This File

Each time we complete a lesson together, I will update this file.
- `[ ]` = Not started
- `[~]` = In progress
- `[x]` = Completed

---

## Stage 1 — Foundations

| # | Topic | Status | Date Completed | Notes |
|---|-------|--------|---------------|-------|
| 1.1 | What is an LLM? | [x] | 2026-05-13 | Learned in README |
| 1.2 | What is RAG? | [x] | 2026-05-13 | Learned in README |
| 1.3 | What is a Workflow? | [x] | 2026-05-13 | Learned in README |
| 1.4 | What is an AI Agent? | [x] | 2026-05-13 | Learned in README |
| 1.5 | Set up Python environment | [x] | 2026-05-13 | Python 3.12.10 + pip 25.0.1 installed via winget |
| 1.6 | Get an API key | [x] | 2026-05-13 | Gemini API key via AI Studio + billing enabled |
| 1.7 | Make your first LLM API call | [x] | 2026-05-13 | Used google-genai SDK with gemini-2.5-flash |
| 1.8 | Understand tokens and costs | [x] | 2026-05-13 | Saw live token counts + cost per call |

---

## Stage 2 — Working with LLMs

| # | Topic | Status | Date Completed | Notes |
|---|-------|--------|---------------|-------|
| 2.1 | Prompt engineering basics | [x] | 2026-05-13 | Zero-shot, few-shot, role prompting, format control |
| 2.2 | System prompts vs user prompts | [x] | 2026-05-13 | Same question, 3 different system prompts = 3 different agents |
| 2.3 | Temperature and parameters | [x] | 2026-05-13 | Temperature 0=deterministic, 2=creative; max_output_tokens hard-caps length |
| 2.4 | Multi-turn conversations | [x] | 2026-05-13 | Chat history sent every turn; built interactive chat loop |
| 2.5 | Structured outputs (JSON) | [x] | 2026-05-13 | response_mime_type forces valid JSON; parsed into Python dicts |

---

## Stage 3 — RAG (Retrieval-Augmented Generation)

| # | Topic | Status | Date Completed | Notes |
|---|-------|--------|---------------|-------|
| 3.1 | What are embeddings? | [x] | 2026-11-23 | gemini-embedding-001 → 3072-dim vectors; cosine similarity ranks by meaning, not words |
| 3.2 | Install and set up ChromaDB | [x] | 2026-11-23 | chromadb 1.5.9; PersistentClient saves to disk; add/query with own Gemini embeddings; metadata filters |
| 3.3 | Load and chunk a document | [x] | 2026-11-23 | Fixed-size cuts mid-word; overlap helps; structure-aware (section + paragraph, title prefix) wins → 11 chunks |
| 3.4 | Store embeddings in the DB | [x] | 2026-11-23 | Load → chunk → embed (RETRIEVAL_DOCUMENT) → upsert with stable ids + metadata; 11 chunks stored, re-runs don't duplicate |
| 3.5 | Query the vector database | [x] | 2026-11-23 | retrieve() with RETRIEVAL_QUERY; finds meaning ("baby"→Parental Leave); missed "$800 monitor" chunk; unanswerable Qs still return chunks → LLM must say "I don't know" |
| 3.6 | Build end-to-end RAG pipeline | [x] | 2026-11-23 | Retrieve top-5 → augment prompt → generate; grounded system prompt cites sources + says "couldn't find" for dental |

---

## Stage 4 — Tools and Function Calling

| # | Topic | Status | Date Completed | Notes |
|---|-------|--------|---------------|-------|
| 4.1 | What is function calling? | [x] | 2026-11-23 | LLM returns a function_call (name + args), OUR code runs it, result goes back, LLM writes answer; LLM decides when a tool is needed |
| 4.2 | Define a tool for the LLM | [x] | 2026-11-23 | Switched to local Ollama (llama3.2:3b). Hand-written tool loop. 3B model can't chain tools → redesigned tools to take a name directly (1 call per task); lookups/actions now work |
| 4.3 | Calculator tool example | [x] | 2026-11-24 | Without tool: refused / $24,819 (wrong). With tool: exact. Safe ast evaluator, never eval(). Model dropped a decimal point → fixed with stricter prompt |
| 4.4 | Web search tool example | [x] | 2026-11-24 | Free DuckDuckGo search (ddgs). Without: "Python 3.10". With: "3.15.2" + source. Search can fail randomly → prompt says retry once & never conclude "doesn't exist"; snippets only, no full pages |
| 4.5 | File read/write tool example | [x] | 2026-11-24 | list/read/write locked to stage4/workspace/ sandbox; blocked path traversal (../../.env) even when the LLM obeyed the request |

---

## Stage 5 — Workflows and Orchestration

| # | Topic | Status | Date Completed | Notes |
|---|-------|--------|---------------|-------|
| 5.1 | Chain two LLM calls | [x] | 2026-11-24 | Extract (pydantic JSON schema + validation gate) → write reply. Chain kept order ID + stuck to policy; big prompt invented a policy detail but kept the birthday context that step 1 dropped |
| 5.2 | Add conditional logic | [x] | 2026-11-24 | Router: escalate / ask for order ID / refund (eligibility in Python) / general. 3B over-labelled "angry" → label definitions + few-shot + code anger check ("LLM AND code must agree") → 4/4 routes correct |
| 5.3 | Parallel steps | [x] | 2026-11-24 | ThreadPoolExecutor fan-out/fan-in. 3 local LLM calls: 9.9s → 9.1s (Ollama/hardware mostly serial). 2 waiting lookups: 4.0s → 2.0s. All 5: 10.6s vs ~13.9s sequential |
| 5.4 | Intro to LangChain | [x] | 2026-11-24 | langchain-core 1.8.4 + langchain-ollama 1.2.0. Rebuilt 5.1–5.3: prompt \| model \| parser, with_structured_output, RunnableParallel, @tool/bind_tools, with_retry, batch. Less code, same ideas; prompt quality still decides results |
| 5.5 | Build a pipeline with LangChain | [x] | 2026-11-24 | 5.2 router as one pipeline: RunnablePassthrough.assign (extract ‖ anger check) → RunnableBranch → routes. 4/4 routes correct; reply writer still invents details ("10-12 business days") |

---

## Stage 6 — Full AI Agent

| # | Topic | Status | Date Completed | Notes |
|---|-------|--------|---------------|-------|
| 6.1 | Combine RAG + tools | [x] | 2026-11-24 | search_handbook (RAG as a tool) + balance + booking. Right tool 5/5; two-part question → 2 independent tools in one turn ✅; extra search for "capital of France" |
| 6.2 | Add short-term memory | [x] | 2026-11-24 | Modes: none / history / rewrite. Memory fixed "And Aisha?" but 3B linked "her" to the wrong person in every mode (and copied example names). Real fix: human confirmation before actions → wrong booking blocked |
| 6.3 | Add long-term memory | [x] | 2026-11-24 | JSON memory file + auto fact extraction after each message + facts in system prompt. New session: "my days" → Aisha ✅. Auto-extraction missed a preference → added reliable 'remember <fact>' command |
| 6.4 | Build a multi-agent system | [x] | 2026-11-24 | Supervisor makes a JSON plan → hr/research/files/math specialists (few tools each). 5/5 routed right. Failed search + invented answer got saved to a file → added a code quality gate that watches tool results and stops the plan |
| 6.5 | Deploy the agent (FastAPI) | [x] | 2026-11-24 | /health, /ask, /actions, /actions/{id}/confirm on 127.0.0.1:8000. input() confirmation → "pending action" + approve endpoint. Supervisor over-planned a files step → sharper specialist descriptions. Booking approved over HTTP: Aisha 12 → 9 |
| 6.6 | Build a simple frontend | [x] | 2026-11-24 | Chat page (stage6/static/index.html) served at / by FastAPI; Approve/Reject buttons for pending bookings; agent text inserted with textContent only (no XSS); light/dark + mobile |

---

## Projects Built

| # | Project Name | Description | Date | Files |
|---|-------------|-------------|------|-------|
| 1 | Nimbus HR Assistant | RAG chatbot answering questions from an employee handbook, with source citations | 2026-11-23 | `stage3/rag.py` (+ ingest.py, query.py, chunking.py, embedder.py) |
| 2 | Support Email Router | Extracts facts from customer emails and routes them (refund / ask for order ID / escalate), by hand and with LangChain | 2026-11-24 | `stage5/router.py`, `stage5/langchain_pipeline.py` |
| 3 | Nimbus HR Agent (web app) | Multi-agent system (HR, research, files, math) with RAG, tools, memory, human approval, a FastAPI backend and a chat web page | 2026-11-24 | `stage6/api.py` + `stage6/static/index.html` (run `python stage6/api.py`, open http://127.0.0.1:8000) |

(We will fill this in as we build things together!)

---

## My Questions and Confusions

Write any questions you have here. We will answer them together.

- *Example: "Why do I need a vector database? Can't I just use a regular database?"*

---

## Wins and Milestones

- **2026-05-13** — Started the journey! Read through all the core concepts.
- **2026-05-13** — Python 3.12.10 installed successfully.
- **2026-05-13** — Made first LLM API call! Gemini 2.5 Flash responded successfully.
- **2026-11-23** — Stage 3 complete! Built a first RAG chatbot that answers from a document and admits when it doesn't know.
- **2026-11-24** — Stage 4 complete! The LLM can now act: look up and update data, calculate, search the web, and manage files, all running locally on Ollama.
- **2026-11-24** — Stage 5 complete! Built workflows by hand (chain, branch, parallel) and then with LangChain.
- **2026-11-24** — 🎓 COURSE COMPLETE! Stage 6 done: a multi-agent HR assistant with RAG, tools, short- and long-term memory, human approval, a web API and a chat page.

---

*You are not behind. You are exactly where you need to be.*
