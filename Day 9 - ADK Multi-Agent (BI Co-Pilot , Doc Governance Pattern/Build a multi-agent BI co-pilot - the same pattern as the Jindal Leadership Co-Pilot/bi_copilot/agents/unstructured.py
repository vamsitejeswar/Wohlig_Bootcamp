import importlib.util
import os
import sys

from google.adk.agents import LlmAgent
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def _import_file(module_name, relative_path):
    abs_path = os.path.normpath(os.path.join(os.path.dirname(__file__), relative_path))
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_d6 = "../../../../Day 6 - RAG with Grounding + Eval (Production-Grade)/Build a RAG chatbot that cites every claim - exactly the pattern behind Meesho Memory and Apollo content search/rag_bot"

_retriever_mod = _import_file("retriever", f"{_d6}/retriever.py")
_generator_mod = _import_file("generator", f"{_d6}/generator.py")

Retriever = _retriever_mod.Retriever
Generator = _generator_mod.Generator

# Initialise once
_retriever = Retriever()
_generator = Generator()


def search_documents(question: str) -> str:
    """
    Search the policy and document knowledge base using vector similarity,
    then generate a grounded answer with inline citations.

    Use this tool for questions about policies, procedures, definitions,
    SLA terms, compliance rules, or any content from PDF documents.
    """
    chunks = _retriever.retrieve(question, top_k=5)

    if not chunks:
        return "No relevant documents found for this question."

    result = _generator.generate(question, chunks)

    if result["is_no_answer"]:
        return result["answer"]

    sources = ", ".join(f"{c.doc_id}:p{c.page}" for c in result["used_chunks"])
    return f"{result['answer']}\n\n[Sources: {sources}]"


unstructured_data_agent = LlmAgent(
    name="unstructured_data_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Document & Policy specialist for a BI Co-Pilot system.\n\n"
        "Your job is to answer questions about policies, procedures, SLA targets,\n"
        "compliance rules, definitions, and any content stored in PDF documents.\n\n"
        "Use search_documents() with the user's exact question as-is.\n"
        "Always include the source citations in your answer exactly as they appear.\n"
        "If no documents match, say clearly: 'No relevant documents found for this question.'"
    ),
    tools=[search_documents],
)
