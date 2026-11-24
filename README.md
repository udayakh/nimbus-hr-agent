# AI Agent Workflow — Zero to Hero Guide

Welcome! This guide is written for complete beginners.
By the end of this journey, you will understand how to build your own AI agents from scratch.

---

## Table of Contents

1. [What is an LLM?](#1-what-is-an-llm)
2. [What is RAG?](#2-what-is-rag)
3. [What is a Workflow?](#3-what-is-a-workflow)
4. [What is an AI Agent?](#4-what-is-an-ai-agent)
5. [How They All Fit Together](#5-how-they-all-fit-together)
6. [Your Learning Roadmap](#6-your-learning-roadmap)
7. [Tools We Will Use](#7-tools-we-will-use)

---

## 1. What is an LLM?

**LLM = Large Language Model**

Think of it like this:

> An LLM is a very smart autocomplete. It has read billions of pages of text (books, websites, code) and learned patterns from all of it. When you type a question, it predicts the best possible answer word by word.

### Real-world examples of LLMs:
| Name | Made By |
|------|---------|
| GPT-4 | OpenAI |
| Claude | Anthropic |
| Gemini | Google |
| Llama | Meta |

### Key things to know:
- You talk to an LLM by sending it a **prompt** (your message/question)
- It replies with a **completion** (its answer)
- The LLM does NOT remember previous conversations unless you send the history along with each message
- It has a **context window** — the maximum amount of text it can read at once (like a whiteboard with limited space)

### Simple analogy:
```
You (prompt) --> [LLM Brain] --> Answer (completion)
```

---

## 2. What is RAG?

**RAG = Retrieval-Augmented Generation**

### The problem RAG solves:
LLMs are trained on data up to a certain date (called the "knowledge cutoff").
They don't know about:
- Your private documents
- Recent news
- Your company's data

### What RAG does:
RAG lets the LLM "look things up" before answering, just like a student who is allowed to use their notes during an exam.

### How RAG works — step by step:

```
Step 1: You have a pile of documents (PDFs, notes, websites)
          ↓
Step 2: Break them into small chunks
          ↓
Step 3: Convert each chunk into numbers (called "embeddings")
        These numbers capture the MEANING of the text
          ↓
Step 4: Store those numbers in a "Vector Database"
          ↓
Step 5: User asks a question
          ↓
Step 6: Search the Vector Database for the most relevant chunks
          ↓
Step 7: Send those chunks + the user's question to the LLM
          ↓
Step 8: LLM answers using the retrieved information
```

### Simple analogy:
Without RAG → You ask a friend a question. They answer from memory only.
With RAG    → You ask a friend. They quickly Google it first, then answer you.

### Key terms:
| Term | Meaning |
|------|---------|
| Embedding | Numbers that represent the meaning of text |
| Vector Database | A database that stores and searches embeddings |
| Chunk | A small piece of a larger document |
| Retrieval | Finding the most relevant chunks for a query |

---

## 3. What is a Workflow?

A **workflow** is a series of steps that happen in a specific order to complete a task.

### Example — a simple customer support workflow:
```
User sends message
      ↓
Classify: Is it a complaint or a question?
      ↓
[If complaint] → Retrieve refund policy → Draft apology → Send
[If question]  → Search FAQ database → Draft answer → Send
```

### In AI, a workflow means:
Chaining multiple LLM calls and tools together so that the output of one step becomes the input of the next.

### Types of workflows:
| Type | Description |
|------|-------------|
| **Sequential** | Steps happen one after another |
| **Parallel** | Multiple steps happen at the same time |
| **Conditional** | Different paths based on conditions (if/else) |
| **Loop** | Repeat a step until a condition is met |

---

## 4. What is an AI Agent?

An **AI Agent** is an LLM that can take actions — not just answer questions.

### The difference:
- **Regular LLM chat**: You ask → It answers → Done
- **AI Agent**: You give a goal → It plans → It uses tools → It takes actions → It checks results → It tries again if needed

### What tools can an agent use?
- Search the web
- Read and write files
- Call an API
- Run code
- Send emails
- Query a database

### The Agent Loop (ReAct pattern):
```
Goal: "Find the weather in Tokyo and save it to a file"

  1. THINK: "I need to search for Tokyo weather"
  2. ACT:   Use the web search tool
  3. OBSERVE: Gets search results
  4. THINK: "Now I need to save this to a file"
  5. ACT:   Use the file write tool
  6. OBSERVE: File saved successfully
  7. THINK: "Goal complete"
  8. DONE
```

This loop is called **ReAct** (Reason + Act).

### Types of agents:
| Type | Description |
|------|-------------|
| **Single Agent** | One LLM doing everything |
| **Multi-Agent** | Multiple specialized agents working together |
| **Autonomous Agent** | Runs on its own with minimal human input |
| **Human-in-the-loop** | Pauses and asks human before important actions |

---

## 5. How They All Fit Together

```
┌─────────────────────────────────────────────────┐
│                  AI AGENT                        │
│                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────────┐  │
│  │  User   │───▶│   LLM   │───▶│   Tools     │  │
│  │  Goal   │    │ (Brain) │    │ (Hands)     │  │
│  └─────────┘    └────┬────┘    └─────────────┘  │
│                      │                           │
│               ┌──────▼──────┐                   │
│               │     RAG     │                   │
│               │  (Memory)   │                   │
│               └─────────────┘                   │
│                                                 │
│  The WORKFLOW connects all of these steps        │
└─────────────────────────────────────────────────┘
```

- **LLM** = The brain (thinks and decides)
- **RAG** = The memory (retrieves relevant knowledge)
- **Tools** = The hands (takes actions in the world)
- **Workflow** = The system that orchestrates everything

---

## 6. Your Learning Roadmap

We will build your knowledge in stages. Track your progress in [progress.md](./progress.md).

### Stage 1 — Foundations (Week 1)
- [ ] Understand what an LLM is
- [ ] Make your first API call to an LLM
- [ ] Learn about prompts and completions
- [ ] Learn about tokens and context windows

### Stage 2 — Working with LLMs (Week 2)
- [ ] Prompt engineering basics
- [ ] System prompts vs user prompts
- [ ] Temperature and other parameters
- [ ] Handling conversations (chat history)

### Stage 3 — RAG (Week 3)
- [ ] What are embeddings?
- [ ] Set up a vector database
- [ ] Load and chunk documents
- [ ] Build a simple RAG pipeline

### Stage 4 — Tools and Function Calling (Week 4)
- [ ] What is function/tool calling?
- [ ] Give the LLM a calculator tool
- [ ] Give the LLM a web search tool
- [ ] Build a simple tool-using agent

### Stage 5 — Workflows and Orchestration (Week 5)
- [ ] Chain multiple LLM calls
- [ ] Build a sequential workflow
- [ ] Add conditional branching
- [ ] Use a framework (LangChain or LlamaIndex)

### Stage 6 — Building a Full Agent (Week 6)
- [ ] Combine RAG + tools + workflow
- [ ] Add memory to your agent
- [ ] Build a multi-agent system
- [ ] Deploy your agent

---

## 7. Tools We Will Use

| Tool | Purpose | Difficulty |
|------|---------|-----------|
| **Python** | Programming language | Beginner |
| **Anthropic SDK** | Talk to Claude (LLM) | Beginner |
| **OpenAI SDK** | Alternative LLM access | Beginner |
| **ChromaDB** | Vector database for RAG | Intermediate |
| **LangChain** | Workflow & agent framework | Intermediate |
| **LlamaIndex** | RAG framework | Intermediate |
| **FastAPI** | Build an API for your agent | Intermediate |

---

## Getting Started

Before writing any code, make sure you have:

1. **Python installed** (version 3.10 or higher)
   ```
   python --version
   ```

2. **pip installed** (Python package manager)
   ```
   pip --version
   ```

3. **An API key** from Anthropic (claude.ai) or OpenAI

We will set up everything together, step by step.
Check [progress.md](./progress.md) to see where we are and what's next.

---

*"Every expert was once a beginner. Let's build something great."*
