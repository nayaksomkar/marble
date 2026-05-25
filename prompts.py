"""
All prompts sent to the LLM. Edit this file to change how the AI behaves.
"""

SYSTEM_PROMPT = (
    "You are a research assistant. Answer the user's question using ONLY "
    "the document context provided below. If the answer is not in the "
    "context, say you couldn't find it in the available documents."
)

CONTEXT_TEMPLATE = "=== DOCUMENT CONTEXT ===\n{context}"


def build_system_message(context: str) -> str:
    """Combine the system prompt with the document context."""
    return f"{SYSTEM_PROMPT}\n\n{CONTEXT_TEMPLATE.format(context=context)}"