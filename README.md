# MedBot Legacy

<p align="center">
  <img src="assets/readme/medbot-rag-banner.png" alt="Abstract illustration of medical documents connected to an AI assistant" width="100%" />
</p>

<p align="center">
  A focused Flask medical-document assistant powered by retrieval-augmented generation (RAG).
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> |
  <a href="#how-it-works">How it works</a> |
  <a href="#deployment">Deployment</a> |
  <a href="#safety">Safety</a>
</p>

## Why this project

MedBot Legacy is the lightweight, server-rendered edition of the medical chatbot. It keeps the original LangChain, Pinecone, Hugging Face, and OpenAI retrieval flow while adding a responsive interface, safer request handling, a health endpoint, automated tests, and deployment assets.

Use it when you want a simple Flask application with no frontend build step.

| Capability | Included |
| --- | --- |
| Medical-document answers grounded in retrieved context | Yes |
| Pinecone similarity search | Yes - existing `medical-chatbot` index |
| Responsive, dependency-free chat interface | Yes |
| Lightweight health check | `GET /health` |
| Docker, Render, and GitHub Actions setup | Yes |

> **Important:** The original retrieval behavior is intentionally preserved: the app retrieves three relevant chunks and uses the existing medical prompt with `gpt-4o`.

## How it works

```text
Question in the browser
        |
        v
Flask /get endpoint validates the message
        |
        v
Hugging Face embeddings + Pinecone retrieval (top 3)
        |
        v
Existing LangChain prompt + OpenAI gpt-4o
        |
        v
Grounded response displayed in the chat
```

The RAG chain is initialized only when a chat request needs it. This lets `/health` respond quickly without contacting OpenAI, Pinecone, or the embedding model.

## Quick start

### 1. Prerequisites

- Python 3.12
- An OpenAI API key
- A Pinecone API key with access to the existing `medical-chatbot` index

### 2. Configure the project

```powershell
git clone https://github.com/firoz1860/Medical-Chatbot-with-LLMs-LangChain-Pinecone-Flask-AWS-.git
cd Medical-Chatbot-with-LLMs-LangChain-Pinecone-Flask-AWS-

py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
Copy-Item .env.example .env
```

Set these values in `.env`:

| Variable | Required | Description |
| --- | --- | --- |
| `OPENAI_API_KEY` | Yes | Key used to generate the final answer. |
| `PINECONE_API_KEY` | Yes | Key used to retrieve medical-document context. |
| `PORT` | No | Local server port; defaults to `8080`. |

Never commit `.env` or a real provider key.

### 3. Test and run

```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe app.py
```

Open [http://localhost:8080](http://localhost:8080). To verify that the service is alive without initializing providers, visit [http://localhost:8080/health](http://localhost:8080/health).

## Using the app

1. Open the chat page in a browser.
2. Ask a focused question related to the indexed medical documents.
3. MedBot retrieves relevant passages before composing its answer.
4. Treat the answer as informational support, not a clinical decision.

The chat endpoint is also available for a compatible form-style request:

```http
POST /get
Content-Type: application/x-www-form-urlencoded

msg=What are the symptoms described in the document?
```

Successful requests return plain-text answers. Blank messages receive a `400`; unavailable or failed model providers receive safe, non-sensitive error responses.

## Quality checks

```powershell
.\.venv\Scripts\python.exe -m pytest -v
.\.venv\Scripts\python.exe -m compileall -q app.py src
```

The GitHub Actions CI workflow runs these checks for pull requests and pushes to `main`.

## Deployment

### Render

The repository includes `render.yaml` for a Flask/Gunicorn service.

1. In Render, create a Blueprint from this repository.
2. Add `OPENAI_API_KEY` and `PINECONE_API_KEY` as service environment variables.
3. Confirm the health-check path is `/health`.
4. Deploy; Render supplies `PORT` automatically.

### Docker

```powershell
docker build -t medbot-legacy .
docker run --rm -p 8080:8080 --env-file .env medbot-legacy
```

### Continuous deployment

The Render deployment workflow runs only after successful CI on `main`. Add `RENDER_DEPLOY_HOOK_URL` as a GitHub repository secret after creating a Render deploy hook. Without that secret, the workflow safely skips the release step.

## Project map

```text
app.py                    Flask app factory, routes, health check, RAG initialization
src/                      Existing LangChain and Pinecone pipeline
templates/chat.html       Accessible chat page
static/style.css          Responsive visual design
tests/test_app.py         Route, error-handling, UI, and deployment tests
render.yaml               Render Blueprint
Dockerfile                Portable Gunicorn image
```

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `503` from a chat request | Confirm `OPENAI_API_KEY` and `PINECONE_API_KEY` are present. |
| Retrieval or provider error | Confirm key permissions and the `medical-chatbot` index availability. |
| Port is unavailable | Set a different `PORT` value in `.env`. |
| Health check passes but chat fails | Expected when the service can start but an external provider is unavailable. |

## Safety

MedBot retrieves content from indexed medical documents and can still be incomplete or wrong. It is not a diagnostic tool and is not a substitute for a licensed medical professional. In an emergency, contact local emergency services or a qualified clinician.
