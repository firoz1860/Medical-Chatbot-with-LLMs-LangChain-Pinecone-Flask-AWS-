# MedBot Legacy Flask RAG

A Flask medical knowledge assistant backed by the existing LangChain, Pinecone, Hugging Face embedding, and OpenAI RAG pipeline. The retrieval and prompt logic are unchanged; this version adds safe request handling, a responsive dependency-free UI, tests, and deployment configuration.

## Local setup

Use Python 3.12, then create a virtual environment and install the runtime dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` and `PINECONE_API_KEY` in `.env`. The app uses the existing `medical-chatbot` Pinecone index, retrieves three chunks, and asks `gpt-4o` with the existing system prompt.

```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe app.py
```

Open `http://localhost:8080`. `GET /health` is a lightweight readiness endpoint and does not contact model providers.

## Deploy to Render

1. Create a Render Blueprint from this repository; Render reads `render.yaml`.
2. Set `OPENAI_API_KEY` and `PINECONE_API_KEY` as Render environment variables.
3. Confirm the service health URL is `/health`.
4. In GitHub Actions, add `RENDER_DEPLOY_HOOK_URL` only after creating a Render deploy hook.

CI runs on pull requests and `main`. The Render hook is called only after a successful CI run on `main`; without the GitHub secret, no release action occurs. `Dockerfile` supplies an equivalent portable Gunicorn container command.

## Safety note

This tool answers from indexed medical documents but can make mistakes. It is not a replacement for a licensed medical professional.
