import ast
from pathlib import Path

import pytest


def test_application_exposes_factory():
    tree = ast.parse(Path("app.py").read_text(encoding="utf-8"))
    assert any(
        isinstance(node, ast.FunctionDef) and node.name == "create_app"
        for node in tree.body
    )


class FakeChain:
    def __init__(self, answer="A chronic airway condition."):
        self.answer = answer
        self.requests = []

    def invoke(self, payload):
        self.requests.append(payload)
        return {"answer": self.answer}


@pytest.fixture
def client():
    from app import create_app

    chain = FakeChain()
    app = create_app(chain_factory=lambda: chain)
    app.config.update(TESTING=True)
    return app.test_client(), chain


def test_health_does_not_build_rag_chain():
    from app import create_app

    def should_not_run():
        raise AssertionError("health must not initialize the RAG chain")

    app = create_app(chain_factory=should_not_run)
    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_chat_invokes_injected_chain(client):
    http_client, chain = client

    response = http_client.post("/get", data={"msg": "What is asthma?"})

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "A chronic airway condition."
    assert chain.requests == [{"input": "What is asthma?"}]


@pytest.mark.parametrize("payload", [{}, {"msg": "   "}])
def test_chat_rejects_missing_or_blank_message(client, payload):
    http_client, _ = client

    response = http_client.post("/get", data=payload)

    assert response.status_code == 400
    assert "message" in response.get_data(as_text=True).lower()


def test_chat_hides_provider_failures():
    from app import MissingConfigurationError, create_app

    def broken_chain_factory():
        raise MissingConfigurationError("OPENAI_API_KEY=super-secret")

    app = create_app(chain_factory=broken_chain_factory)
    app.config.update(TESTING=True)
    response = app.test_client().post("/get", data={"msg": "Question"})

    assert response.status_code == 503
    assert "super-secret" not in response.get_data(as_text=True)

def test_chat_template_uses_safe_dom_and_no_jquery():
    template = Path("templates/chat.html").read_text(encoding="utf-8")

    assert "jquery" not in template.lower()
    assert "innerHTML" not in template
    assert "textContent" in template

def test_deployment_assets_are_secret_free():
    deployment_files = [
        Path("Dockerfile"),
        Path("render.yaml"),
        Path(".github/workflows/ci.yml"),
        Path(".github/workflows/deploy-render.yml"),
    ]

    for file_path in deployment_files:
        assert file_path.is_file()
        assert "sk-" not in file_path.read_text(encoding="utf-8")


def test_render_deploy_secret_is_not_used_in_a_job_condition():
    workflow = Path(".github/workflows/deploy-render.yml").read_text(encoding="utf-8")
    assert "secrets.RENDER_DEPLOY_HOOK_URL != ''" not in workflow
    assert "if: env.RENDER_DEPLOY_HOOK_URL != ''" in workflow
