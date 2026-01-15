# AI Agent Standards for Trainium Job Center

This project has migrated from multi-agent frameworks (CrewAI) to a **Stateful Flow-as-Code** architecture using **LangGraph**, **LangFlow**, and **Langfuse**.

## Core Principles

1. **Flow-as-Code (LangGraph)**: All complex reasoning should be modeled as state machines (Graphs). This provides explicit control over loops, retries, and state persistence.
2. **Visual Prototyping (LangFlow)**: Use LangFlow locally to visualize and test complex graph structures, especially for flows with nested loops.
3. **Prompt Management (Langfuse)**: **NEVER** hardcode prompts. All prompts must be managed in Langfuse under appropriate namespaces (e.g., `jobs/gatekeeper`).
4. **Model Portability (LiteLLM)**: All AI calls must go through `AIService.execute_prompt()`. This ensures unified logging, model hot-swapping, and structured JSON output.

## Directory Structure

- `app/services/ai/`: Core AI infrastructure (`AIService`, `WebSearchTool`).
- `app/services/fit_review/`: The first production implementation of the new standard.
- `app/services/crewai/`: **[DEPRECATED]** Legacy multi-agent implementations. Do not add new features here.

## Deployment Checklist

- [ ] Prompts created/updated in Langfuse (Production label).
- [ ] State schema defined using Pydantic.
- [ ] Nodes are discrete, testable functions in `app/services`.
- [ ] Graph execution wrapped in Langfuse observation for full visibility.
