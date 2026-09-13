# HackerRank Orchestrate Hackathon — Agent System Architecture Context

## 1. Project Overview

You are an expert AI Engineering Assistant helping me build an end-to-end, production-grade AI Agent for the **HackerRank Orchestrate Competition**.

The core goal of this project is to solve a real-world task by designing a resilient, deterministic, and traceable **Agentic System**.

---

## 2. Core Architectural Philosophy

To maximize our evaluation score with the AI Judge, we strictly follow this architectural pattern:

> **"Let the LLM describe, let deterministic code decide."**

### Core Principles:

1. **Strict Separation of Concerns:**
   - **LLMs (Groq API):** Responsible ONLY for perception, parsing unstructured text/data, semantic analysis, and returning validated **Structured Outputs** (Pydantic models).
   - **Deterministic Python Code:** Responsible for all execution logic, decision trees, calculations, condition checks, and state transitions.

2. **Zero Hallucination Tolerance:** No critical decision (e.g., routing, calculations, executing actions) should rely directly on free-text LLM generation.

3. **Prompt Injection Resilience:** Sanitize all input context. Treat external user inputs as untrusted data that must never alter system instructions or prompt flows.

4. **Fault Tolerance & Reliability:**
   - Enforce automatic retries for malformed LLM responses using validated schemas.
   - Fallback mechanisms for API rate limits and unexpected outputs.

5. **Full Observability & Traceability:**
   - Log every internal step, state change, and LLM input/output using `loguru`.
   - Maintain clean transcripts for evaluation.

---

## 3. Technology Stack (100% Free Tier Compliant)

- **Primary LLM Provider:** Groq API (e.g., `llama-3.3-70b-versatile`, `mixtral-8x7b-32768`)
- **Structured Outputs & Validation:** `pydantic` & `instructor`
- **Programming Language:** Python 3.10+
- **Logging & Tracing:** `loguru`
- **Environment Management:** `python-dotenv`

---

## 4. Expected Code Structure & Modularity

Organize the codebase into modular components:
├── .env # API keys (GROQ_API_KEY)
├── config.py # Client initialization & global parameters
├── logger.py # Loguru logger setup (writes to stdout & agent_execution.log)
├── schemas.py # Pydantic models for structured output extraction
├── agent.py # Core agentic loop & LLM call wrappers using Instructor
├── logic.py # Deterministic Python business logic & decision rules
├── main.py # Application entry point & orchestration loop
├── requirements.txt # Project dependencies
└── README.md # System architecture & execution instructions for submission

---

## 5. Instructions for the AI IDE / Copilot

When I provide the problem statement or task details:

1. **Analyze First:** Break down the core problem into inputs, extraction steps, deterministic decision logic, and expected outputs.
2. **Design Schemas (`schemas.py`):** Define strict Pydantic models with `Field(description=...)` attributes for typed extraction.
3. **Implement Extraction (`agent.py`):** Write functions using `instructor` + Groq to parse raw inputs into the Pydantic schemas.
4. **Implement Deterministic Logic (`logic.py`):** Write standard Python functions that execute pure logic based on validated schemas.
5. **Add Comprehensive Logging:** Ensure every state transition is logged cleanly for auditing.
6. **Code Quality:** Keep code production-ready, typed, and well-documented. Avoid unnecessary dependencies or over-engineering.

---

## 6. How We Will Work Together

When I paste the problem statement below, your first response should be:

1. A brief summary of the problem and the proposed architecture.
2. Proposed Pydantic schemas (`schemas.py`).
3. Proposed deterministic execution rules (`logic.py`).
