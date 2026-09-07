# Legacy Medical Chatbot Hardening Design

## Purpose

Make the Flask/LangChain/Pinecone chatbot safe to run and pleasant to use without changing its medical RAG logic. It will still retrieve three similar chunks from the current `medical-chatbot` Pinecone index and use the unchanged `system_prompt` and `gpt-4o` chain.

## Architecture

`app.py` becomes an application-factory-friendly Flask entrypoint. It retains `GET /` and form-compatible `POST /get`, adds `GET /health`, validates a non-empty message, and loads the expensive Pinecone/LangChain chain only for valid chat requests. Environment keys are read without writing `None` into `os.environ`; startup errors become safe user-facing errors while diagnostic details are logged server-side.

The static page becomes a dependency-free responsive interface. It posts the same `msg` form field to `/get`, inserts message text with DOM APIs rather than interpolated HTML, prevents duplicate sends while a request is pending, and presents a readable failed-request state. It shows an advisory that the assistant is not a substitute for a clinician.

## Runtime and Deployment

The service runs with Gunicorn in production and never enables Flask debug mode from source. A Render Blueprint declares the Python web service, a Dockerfile provides a portable container path, and GitHub Actions performs syntax, unit, and dependency checks on pull requests and `main`. A deploy-hook workflow runs only after CI succeeds on `main` and only when `RENDER_DEPLOY_HOOK_URL` is configured as a GitHub Actions secret.

Production supplies `OPENAI_API_KEY`, `PINECONE_API_KEY`, and optional `PORT`; no credentials, deploy hooks, or provider tokens are committed. `PINECONE_INDEX` remains the current fixed index unless a later approved task changes it.

## Error Handling

- Blank or missing `msg` returns HTTP 400 with a concise text error, preserving the text response shape used by the browser.
- Invalid or missing provider configuration returns a generic 503 response; secret values and stack traces never reach a browser.
- Retrieval/model exceptions return a generic 502 response and are logged with a stack trace.
- `GET /health` reports process readiness without initializing embeddings, Pinecone, or OpenAI.

## Verification

Pytest coverage will exercise page and health routes, malformed and blank chat requests, lazy-chain execution with a fake chain, and safe external-service failure handling. The UI will be statically checked for no jQuery/remote scripts and safe DOM insertion. CI must pass Python compilation and pytest before a deployment hook can run.
