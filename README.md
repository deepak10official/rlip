# Billing Agents

Agentic invoice validation workflow using the OpenAI Agents SDK.

The app validates whether an invoice was correctly generated from four document groups:

- Service agreement / contract
- Invoice
- Raw billing evidence
- Payment record

If the invoice is invalid, the workflow explains why and asks a corrected invoice agent to generate a draft corrected invoice structure for finance review.

## Project Structure

```text
backend/
  agents/          OpenAI Agent definitions and guardrails
  orchestration/   Tracing, memory, and end-to-end workflow
  prompts/         Agent prompts
  schemas.py       Pydantic structured output models
  document_loader.py
frontend/
  streamlit_app.py
documents/         Sample billing corpus
```

## Setup

Use the existing virtual environment:

```bash
source .venv/bin/activate
uv pip install -r requirements.txt
```

Create `.env` with:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o
OPENAI_FAST_MODEL=gpt-4o-mini
```

## Run Application

You need two terminal windows to run both the backend and the frontend.

**Terminal 1: Start the FastAPI backend**

```bash
source .venv/bin/activate
uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

*The backend will be available at `http://127.0.0.1:8000`.*

**Terminal 2: Start the Frontend**

Serve the custom HTML/JS frontend using Python's built-in HTTP server:

```bash
python -m http.server 8080 --directory frontend
```

Open your browser and navigate to:

```text
http://127.0.0.1:8080
```


Useful API endpoints:

```text
GET  /health
GET  /billing-types
GET  /billing-types/{billing_type}/rules
GET  /billing-types/{billing_type}/documents
POST /audit/corpus
POST /audit/upload
```

## Run CLI

List billing types:

```bash
source .venv/bin/activate
python -m backend.main --list
```

Inspect sample documents without calling OpenAI:

```bash
source .venv/bin/activate
python -m backend.main --billing-type arc --inspect-docs
```

Inspect the sample-derived billing rules without calling OpenAI:

```bash
source .venv/bin/activate
python -m backend.main --billing-type arc --show-rules
```

Run an agent audit on the sample corpus:

```bash
source .venv/bin/activate
python -m backend.main --billing-type arc
```

## Workflow

1. Vision document reader agent reads rendered document preview images using `OPENAI_VISION_MODEL`.
2. Document intake agent summarizes the four document groups from the vision extraction.
3. The orchestrator injects sample-derived billing rules for the selected billing type.
4. Contract rule agent extracts billing rules from the agreement.
5. Evidence validation agent extracts delivered, consumed, accepted, or rejected work facts.
6. Invoice validation agent decides whether the invoice is valid, invalid, or needs review.
7. Payment reconciliation agent checks payment status separately.
8. Corrected invoice generation agent drafts a corrected invoice when the original is invalid.
9. Final report agent produces the structured output.

The workflow uses SDK tracing through `trace(...)`, persistent file-backed session memory in `.agent_memory/`, guardrails, and Pydantic output models.

## Vision Reading

Set the document-reading model with:

```text
OPENAI_VISION_MODEL=gpt-5.5
```

The current source files are DOCX, XLSX, and EML. Because this machine does not have a native Office renderer, the backend creates page-like PNG previews and sends those images to the vision agent. The downstream agents use that vision extraction as the primary reading source.
