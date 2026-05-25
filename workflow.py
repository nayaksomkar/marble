"""
LangGraph workflow: retrieves document context from SQLite and
uses a Groq / Mistral LLM to answer the user's query.
"""
import json
import logging
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

from pathlib import Path
from config import settings
from prompts import build_system_message

logger = logging.getLogger(__name__)


# ── State ─────────────────────────────────────────────────────────────

class WorkflowState(TypedDict):
    query: str
    context: str
    provider: str
    model: str
    temperature: float
    answer: str
    error: Optional[str]


# ── LLM helpers ───────────────────────────────────────────────────────

def _build_groq_llm(model: str, temperature: float):
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=model or settings.LLM_MODEL,
        temperature=temperature or settings.LLM_TEMPERATURE,
        api_key=settings.GROQ_API_KEY,
    )


def _build_mistral_llm(model: str, temperature: float):
    from langchain_mistralai import ChatMistralAI
    return ChatMistralAI(
        model=model or "mistral-small-latest",
        temperature=temperature or settings.LLM_TEMPERATURE,
        api_key=settings.MISTRAL_API_KEY,
    )


def _get_llm(provider: str, model: str, temperature: float):
    provider = (provider or settings.LLM_PROVIDER).lower()
    if provider == "mistral":
        return _build_mistral_llm(model, temperature)
    return _build_groq_llm(model, temperature)


# ── Nodes ─────────────────────────────────────────────────────────────

def retrieve_context(state: WorkflowState) -> dict:
    """Read all .txt files from uploads/ as context."""
    upload_dir = Path("./uploads")
    parts = []
    for txt_file in sorted(upload_dir.glob("*.txt")):
        text = txt_file.read_text(encoding="utf-8", errors="ignore")
        if text.strip():
            parts.append(f"--- {txt_file.name} ---\n{text[:3000]}")

    context = "\n\n".join(parts) if parts else ""
    if not context:
        context = "[No .txt files found in uploads/. Place .txt files there first.]"

    logger.info(f"Read {len(context)} chars from {len(parts)} .txt files")
    return {"context": context}


def generate_answer(state: WorkflowState) -> dict:
    """Ask the LLM to answer based on document context."""
    system_msg = build_system_message(state["context"])
    system_prompt = SystemMessage(content=system_msg)
    human_msg = HumanMessage(content=state["query"])

    llm = _get_llm(state["provider"], state["model"], state["temperature"])
    try:
        response = llm.invoke([system_prompt, human_msg])
        answer = response.content
    except Exception as e:
        logger.error(f"LLM error: {e}")
        answer = f"Error calling LLM: {e}"
        return {"answer": answer, "error": str(e)}

    return {"answer": answer, "error": None}


# ── Graph ─────────────────────────────────────────────────────────────

def build_workflow() -> StateGraph:
    builder = StateGraph(WorkflowState)

    builder.add_node("retrieve", retrieve_context)
    builder.add_node("generate", generate_answer)

    builder.set_entry_point("retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", END)

    return builder.compile()


# ── Public API ────────────────────────────────────────────────────────

def run_workflow(query: str, provider: str = "", model: str = "",
                 temperature: float = 0.0) -> dict:
    """
    Execute the LangGraph workflow and return the result.
    """
    graph = build_workflow()
    initial = WorkflowState(
        query=query,
        context="",
        provider=provider,
        model=model,
        temperature=temperature or settings.LLM_TEMPERATURE,
        answer="",
        error=None,
    )
    result = graph.invoke(initial)
    return result