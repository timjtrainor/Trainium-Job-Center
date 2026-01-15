# LangFlow + LangGraph + Langfuse: Workflow Guide

This guide explains how to manage, visualize, and execute AI workflows in the Trainium Job Center.

## 1. Local Visualization with LangFlow

We use **LangFlow** as a local "Development Canvas" to map out complex flows.

### How to use

1. **Start LangFlow**: Run `langflow run` in your terminal.
2. **Open UI**: Navigate to `http://127.0.0.1:7800`.
3. **Design**: Drag components (Prompts, Models, Tools) onto the canvas.
4. **Export/Reference**: Once the visual flow is stable, export the JSON and use the **"LangFlow to LangGraph Transpiler"** prompt to convert the blueprint into Python code.

## 2. The Transpiler Protocol

To maintain a high-quality codebase, we do not run LangFlow files directly. Instead:

- **Input**: LangFlow JSON export + Current Graph State definition.
- **Process**: Pass these to the AI Assistant with the "Code-First Transpiler" instruction.
- **Output**: Clean, idiomatic LangGraph `StateGraph` implementation with async nodes.

## 3. Stateful Execution with LangGraph

While LangFlow is for design, **LangGraph** is for production execution.

- **State Machine**: Workflows are modeled as "Graphs" where each step is a "Node".
- **Resilience**: Every step is checkpointed, allowing for robust retries and long-running loops (like the Resume Builder).
- **Code-First**: The backend logic stays in Python (`app/services/*/workflow_service.py`).

## 4. Prompt Management with Langfuse

**Never** edit prompts in Python code.

1. **Tune in Langfuse**: Go to your Langfuse dashboard to edit prompts in the `jobs/` folder.
2. **Model Power**: Change models (e.g., GPT-4 to Gemini) directly in the Langfuse UI.
3. **Hot Reload**: The Python worker will automatically fetch the latest prompt version on the next run—no restart needed.

## 4. Multi-Model Support (LiteLLM)

All nodes use `AIService.execute_prompt()`, which uses **LiteLLM**.

- This ensures your workflow is **model-agnostic**.
- You can route different tasks to different models based on cost/reasoning needs.

## 5. Observability

Every execution is traced. You can see the entire "thought process" of the graph in Langfuse, including:

- Input/Output of every node.
- Exact search results from `WebSearchTool`.
- AI rationales and token usage.
