# Legacy Medical Chatbot Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the legacy Flask medical RAG app safe, testable, responsive, and ready for CI/CD without changing retrieval or answer logic.

**Architecture:** Keep the existing LangChain, Pinecone, embedding, prompt, model, and `POST /get` form contract. Isolate Flask request handling from lazy RAG-chain construction, replace unsafe browser rendering with vanilla DOM code, and deploy with Gunicorn/Render.

**Tech Stack:** Python 3.11, Flask, LangChain, Pinecone, OpenAI, pytest, HTML/CSS/JavaScript, GitHub Actions, Render, Docker.

**Spec:** `docs/superpowers/specs/2026-09-07-legacy-hardening-design.md`

## Global Constraints

- Do not change `src/prompt.py`, the `medical-chatbot` index, the `k=3` retrieval setting, embedding model, or `gpt-4o` selection.
- Preserve `POST /get` accepting a form field named `msg` and returning plain text on success.
- Never commit secrets or provider URLs; use environment variables and GitHub Actions secrets.
- Do not initialize model, OpenAI, or Pinecone resources for `GET /health`.

---

### Task 1: Testable Flask entrypoint and safe chat errors

**Files:**
- Create: `tests/test_app.py`
- Modify: `app.py`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: `POST /get` with `msg` form data.
- Produces: `create_app(chain_factory: Callable[[], Any] | None) -> Flask`, `GET /health`, and text chat responses.

- [ ] **Step 1: Write the failing route tests**

```python
class FakeChain:
    def invoke(self, payload):
        assert payload == {"input": "What is asthma?"}
        return {"answer": "A chronic airway condition."}


def test_chat_invokes_injected_chain(client):
    response = client.post("/get", data={"msg": "What is asthma?"})
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "A chronic airway condition."
```

- [ ] **Step 2: Run the failing test**

Run: `py -m pytest tests/test_app.py -v`

Expected: FAIL because the module initializes remote RAG dependencies at import and has no injectable factory.

- [ ] **Step 3: Implement the minimal factory and handler**

```python
def create_app(chain_factory=None):
    app = Flask(__name__)
    app.config["CHAIN_FACTORY"] = chain_factory or build_rag_chain
    # register /, /health and /get
    return app
```

`/get` strips `request.form.get("msg", "")`, returns 400 for blank input, caches one successfully created chain in `app.extensions`, returns generic 503 for missing configuration and generic 502 for invocation failure, and logs exceptions with `exc_info=True`.

- [ ] **Step 4: Run route tests and syntax checks**

Run: `py -m compileall -q app.py src; py -m pytest tests/test_app.py -v`

Expected: PASS with no real provider access.

- [ ] **Step 5: Commit the route hardening**

```bash
git add app.py requirements.txt tests/test_app.py
git commit -m "feat: harden legacy chat endpoint"
```

### Task 2: Dependency-free safe chat interface

**Files:**
- Modify: `templates/chat.html`
- Modify: `static/style.css`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: `POST /get` plaintext response and non-200 response text.
- Produces: accessible form submission, pending state, and XSS-safe message nodes.

- [ ] **Step 1: Write failing static-safety assertions**

```python
def test_chat_template_uses_safe_dom_and_no_jquery():
    template = Path("templates/chat.html").read_text(encoding="utf-8")
    assert "jquery" not in template.lower()
    assert "innerHTML" not in template
    assert "textContent" in template
```

- [ ] **Step 2: Run the failing assertion**

Run: `py -m pytest tests/test_app.py::test_chat_template_uses_safe_dom_and_no_jquery -v`

Expected: FAIL because the current page imports jQuery and interpolates message HTML.

- [ ] **Step 3: Implement semantic static HTML, CSS, and fetch script**

Use a native form, `fetch('/get', { method: 'POST', body: new FormData(form) })`, `document.createElement`, and `textContent`. Disable the submit button during a request, restore focus afterward, and include `aria-live="polite"` on the message region.

- [ ] **Step 4: Re-run static assertions and route tests**

Run: `py -m pytest tests/test_app.py -v`

Expected: PASS.

- [ ] **Step 5: Commit the UI refresh**

```bash
git add templates/chat.html static/style.css tests/test_app.py
git commit -m "feat: refresh legacy chat interface"
```

### Task 3: CI/CD and deployment documentation

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy-render.yml`
- Create: `Dockerfile`
- Create: `render.yaml`
- Create: `.env.example`
- Modify: `README.md`

**Interfaces:**
- Consumes: repository pushes and optional `RENDER_DEPLOY_HOOK_URL` GitHub secret.
- Produces: a passing CI status and a post-CI Render deploy-hook request on `main`.

- [ ] **Step 1: Write a failing configuration test**

```python
def test_deployment_files_do_not_contain_secrets():
    for path in ["render.yaml", ".github/workflows/deploy-render.yml"]:
        assert "sk-" not in Path(path).read_text(encoding="utf-8")
```

- [ ] **Step 2: Run the failing configuration test**

Run: `py -m pytest tests/test_app.py::test_deployment_files_do_not_contain_secrets -v`

Expected: FAIL because the deployment files do not exist.

- [ ] **Step 3: Add deploy assets**

Configure Render to build `pip install -r requirements.txt` and start `gunicorn --bind 0.0.0.0:$PORT app:app`. Configure Docker with a non-root production command. CI installs requirements and pytest, compiles source, and runs pytest. The deploy workflow uses `curl --fail --silent --show-error -X POST "$RENDER_DEPLOY_HOOK_URL"` only when the hook secret is non-empty and only after CI succeeds on `main`.

- [ ] **Step 4: Verify all local checks**

Run: `py -m compileall -q app.py src; py -m pytest -v`

Expected: PASS.

- [ ] **Step 5: Commit deployment readiness**

```bash
git add .github Dockerfile render.yaml .env.example README.md tests/test_app.py
git commit -m "ci: add legacy deployment pipeline"
```
