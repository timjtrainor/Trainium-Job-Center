# AGENTS & INTEGRATION DOCUMENTATION

> [!IMPORTANT]
> **Architecture Update (Jan 2026)**: We follow a "Contract-First" pattern. The Python backend is a thin execution layer. All prompt logic, model configuration (temperature, model name), and schema definitions live in Langfuse.

## 1. The Contract-First Pattern

### Fetching Prompts

We use `langfuse.get_prompt(name, label="production")` to retrieve the "Contract".
This contract includes:

- **Compile Template**: The handlebars string.
- **Config**: Model, temperature, max_tokens, and tools.
- **Schema**: Valid JSON schema for structured outputs.

### Passing Dynamic Config

The React frontend passes `variables` to fill the template.
It does **NOT** hardcode model names (unless using a specific override for debugging).

```typescript
// Frontend
await geminiService.executeAiPrompt({
    promptName: "job-analysis-v2",
    variables: { job_description: "..." }
});
```

### OTel Tracing Signature

All backend execution MUST be wrapped in a Langfuse observation span to ensure visibility.

```python
# Backend (ai_service.py)
with lf.start_as_current_observation(name="api_job-analysis-v2", ...) as span:
    prompt = lf.get_prompt("job-analysis-v2")
    # ... execution ...
    span.update(output=...)
```

## 2. Model Configuration

Langfuse `config` object drives execution.

- `model`: "gemini/gemini-1.5-pro", "openai/gpt-4o", etc.
- `temperature`: float
- `max_tokens`: int (optional)
- `json_schema`: object (force structured output)

**No global model aliases** should be used in the Python service unless strictly necessary for legacy routing.

## 3. Observability & Logging

- **Frontend**: API Request payload and Response/Error status are logged to `console`.
- **Backend**: All traces are sent to Langfuse.
- **Silent Failures**: The UI MUST display a clear error if the API returns 500/400.

## 4. Deprecated Patterns

- **Legacy Frameworks**: We have deprecated all heavy-weight agent frameworks (including CrewAI) in favor of the single-purpose, highly reliable prompt chains documented above.
- **Hardcoded Prompts**: Do not write prompt strings in Python/TS files.

## 5. Verification & Testing

The backend includes a robust **Test Harness** to verify any prompt without touching the UI.

```bash
# General Execution
docker exec trainium_python_service python scripts/test_prompt.py "company/web-research" --vars '{"company_name": "Google"}'

# Test with specific Model Overrides (verify and debug plumbing)
docker exec trainium_python_service python scripts/test_prompt.py "company/web-research" --model "openai-test"
docker exec trainium_python_service python scripts/test_prompt.py "company/web-research" --model "gemini-test"
docker exec trainium_python_service python scripts/test_prompt.py "company/web-research" --model "bedrock-test"
```

## 6. Advanced Features (2026 Resilience)

### Variable Case-Bridging

The AI Service automatically bridges naming conventions. If you pass `company_name` from the UI, it will automatically satisfy `{{CompanyName}}` and `{{COMPANY_NAME}}` in your Langfuse prompt.

### Self-Healing JSON

If a model wraps JSON in markdown blocks (e.g. ` ```json ... ``` `), the service automatically extracts and parses the core JSON object.

### Tool Normalization

## 7. DB-AI Alignment & Schema Mapping

### The "Source" Rule

All AI-generated intelligence is stored with source attribution.

- **Postgres Column**: `text` or `jsonb`
- **Frontend Type**: `InfoField { text: string, source: string | string[] }`
- **DB Rule**:
  - If the column is `jsonb`: Store the `InfoField` object directly.
  - If the column is `text` (e.g. `funding_status`): Store the **JSON stringified** version of the `InfoField` object use `JSON.parse` on the frontend.
  - Default `source` for manual edits: `"manual"`

### Column Mapping Strategy

| AI Key | DB Column | Type | Notes |
| :--- | :--- | :--- | :--- |
| `funding_status` | `funding_status` | `text` | **JSON-in-Text**. Must parse. |
| `competitors` | `competitors` | `jsonb` | Object with `text` (comma-separated list). |
| `strategic_initiatives` | `strategic_initiatives` | `jsonb` | Standard `InfoField`. |
| `known_tech_stack` | `known_tech_stack` | `jsonb` | Standard `InfoField`. |

## 8. Consultant-Led Interview Standard

As of Jan 2026, all interview preparation agents must adhere to the "Consultative Diagnosis" framework.

### Strategic Pivot: "Selling a Solution"

- **Focus**: Strategic intervention vs. Achievement listing.
- **Tone**: Executive Peer-to-Peer (Modern Carnegie style).
- **Core Assets**:
    1. **Scripted Opener (3-part)**:
        - **Hook**: Pivot to the company's macro challenge.
        - **Bridge**: Link background to their core problem.
        - **Pivot**: Hand back the conversation with a diagnostic question.
    2. **Diagnostic Battle Map**:
        - Explicit mapping of **Company Pathology** (Pain/Friction) to **Proposed Intervention** (Your solution).

### Prompt Contract: `interview/consultant-blueprint`

- **Input Variables**: `JOB_DESCRIPTION`, `COMPANY_DATA_JSON`, `CAREER_DNA_JSON`, `JOB_PROBLEM_ANALYSIS_JSON`.
- **Primary Schema**: Matches the `InterviewStrategy` model with `scripted_opening` and `diagnostic_matrix`.
