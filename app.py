import logging
import os
from typing import Any, Callable

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request


load_dotenv()

INDEX_NAME = "medical-chatbot"
logger = logging.getLogger(__name__)


class MissingConfigurationError(RuntimeError):
    """Raised when a required provider credential is not configured."""


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise MissingConfigurationError(f"{name} is not configured")
    return value


def build_rag_chain() -> Any:
    """Build the existing medical RAG chain only when a chat request needs it."""
    _require_env("PINECONE_API_KEY")
    _require_env("OPENAI_API_KEY")

    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_pinecone import PineconeVectorStore
    from src.helper import download_hugging_face_embeddings
    from src.prompt import system_prompt

    embeddings = download_hugging_face_embeddings()
    docsearch = PineconeVectorStore.from_existing_index(INDEX_NAME, embedding=embeddings)
    retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    chat_model = ChatOpenAI(model="gpt-4o")
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("human", "{input}")])
    question_answer_chain = create_stuff_documents_chain(chat_model, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


def _get_rag_chain(app: Flask) -> Any:
    chain = app.extensions.get("rag_chain")
    if chain is None:
        chain = app.config["RAG_CHAIN_FACTORY"]()
        app.extensions["rag_chain"] = chain
    return chain


def create_app(chain_factory: Callable[[], Any] | None = None) -> Flask:
    """Create the Flask app without eagerly initializing external RAG services."""
    app = Flask(__name__)
    app.config["RAG_CHAIN_FACTORY"] = chain_factory or build_rag_chain

    @app.get("/")
    def index():
        return render_template("chat.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/get")
    def chat():
        message = request.form.get("msg", "").strip()
        if not message:
            return "A message is required.", 400

        try:
            response = _get_rag_chain(app).invoke({"input": message})
            return str(response["answer"])
        except MissingConfigurationError:
            logger.warning("Chat request rejected because provider credentials are missing")
            return "The service is not configured yet.", 503
        except Exception:
            logger.exception("Legacy RAG chat request failed")
            return "I couldn't complete that request. Please try again shortly.", 502

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=False)
