Project Context: Akashi AI Orchestrator

1. Mission Statement:
Building Akashi, a high-control, multi-agent AI system designed to orchestrate local PC operations and cloud services. Unlike "chatbots," Akashi is a "Conductor" that manages manual scripts, system commands, and APIs with a focus on Security, Privacy, and Human-in-the-Loop control.

2. Core Architecture:

Framework: PydanticAI (chosen for strict typing, low overhead, and developer control).

LLM Integration: Hybrid approach using Google Gemini 1.5 Flash/Pro (via Google Generative AI SDK) for reasoning and Ollama for local dev/testing.

Multi-Agent Pattern: A Manager-Worker (Supervisor) hierarchy:

Planner Agent: Decomposes user intent into a structured list of tasks.

Executor Agent: Maps tasks to real-world functions via a Tool Registry.

Privacy/Validator Agents: Handle data masking and output verification.

3. Key Differentiators (Unique Selling Points):

Data Privacy Guard: A local pre-processor that masks PII (API keys, passwords, sensitive data) before sending prompts to cloud LLMs.

Dynamic Tool Registry: Tools are not hard-coded but loaded dynamically. New Python scripts (skills) can be added to a "skills/" folder and whitelisted via a JSON config without restarting the system.

Human-in-the-Loop (HITL): Critical actions (file deletion, system changes) require explicit user confirmation.

Strategy Pattern Execution: Cross-platform support (Windows, macOS, Linux) using specialized OS Handlers.

Local Memory (RAG): Long-term context storage using Vector DBs (ChromaDB/FAISS) and SQLite to remember past interactions.

4. Technical Stack:

Language: Python 3.10+

Validation: Pydantic v2 (for type-safe AI responses).

Infrastructure: Redis (for state management), JSON-based Whitelisting, and Shell/Python subprocess execution.

5. Current Development Phase:

Week 1 Goal: Implementing the Execution Layer. Setting up the Abstract OS Strategy, the Tool Registry, and the Dynamic Whitelist validator.

Next Step: Integrating the PydanticAI Planner to translate natural language into the Task schema.