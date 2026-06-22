"""
generator.py
------------
Step 2 of RAG: Take the question + retrieved chunks, call Gemini,
return a grounded answer with inline citations.

Exports:
  - NO_ANSWER_PHRASE   str    (used by app.py to detect "I don't know" responses)
  - Generator          class  (.generate(question, chunks) → dict)
"""

import os
from pathlib import Path

from google import genai
from dotenv import load_dotenv

from retriever import RetrievedChunk

load_dotenv()

# The exact phrase Gemini must say when the answer isn't in the documents.
# app.py checks for this to show a warning icon.
NO_ANSWER_PHRASE = "I couldn't find this information in the provided documents."


class Generator:
    """
    Wraps Gemini generation with a strict grounding prompt.
    Every answer must cite sources as [doc_id:page] or say NO_ANSWER_PHRASE.
    """

    def __init__(self):
        self.project_id = os.getenv("PROJECT_ID")
        self.location   = os.getenv("LOCATION", "us-central1")

        self.client = genai.Client(
            vertexai=True, project=self.project_id, location=self.location
        )

        # Load grounding rules from system_prompt.md
        self.system_prompt = (
            Path(__file__).parent / "system_prompt.md"
        ).read_text()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _format_chunks(self, chunks: list[RetrievedChunk]) -> str:
        """
        Format retrieved chunks into a numbered context block.

        Example:
            [1] Source: doc3 | Page: 5
            Wide neural networks in the feature-learning regime...

            [2] Source: doc1 | Page: 2
            The Föllmer process is a Brownian motion...
        """
        lines = []
        for i, chunk in enumerate(chunks, start=1):
            lines.append(f"[{i}] Source: {chunk.doc_id} | Page: {chunk.page}")
            lines.append(chunk.text)
            lines.append("")  # blank line between chunks
        return "\n".join(lines)

    # ── Public API ────────────────────────────────────────────────────────────

    def generate(self, question: str, chunks: list[RetrievedChunk]) -> dict:
        """
        Generate a grounded answer.

        Returns a dict with:
          - answer       (str)  : the answer text with [doc_id:page] citations
          - used_chunks  (list) : the chunks that were passed as context
          - is_no_answer (bool) : True if the bot said it couldn't find the answer
        """

        # If retriever returned nothing, skip the LLM call entirely
        if not chunks:
            return {
                "answer":       NO_ANSWER_PHRASE,
                "used_chunks":  [],
                "is_no_answer": True,
            }

        # Build the full prompt: system rules + context + question
        context = self._format_chunks(chunks)
        full_prompt = f"""{self.system_prompt}

--- CONTEXT START ---
{context}
--- CONTEXT END ---

Question: {question}

Answer:"""

        # Call Gemini
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )

        # response.text can be None for thinking models if output is empty
        answer = (response.text or "").strip()
        if not answer:
            answer = NO_ANSWER_PHRASE

        is_no_answer = NO_ANSWER_PHRASE.lower() in answer.lower()

        return {
            "answer":       answer,
            "used_chunks":  chunks,
            "is_no_answer": is_no_answer,
        }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from retriever import Retriever

    retriever = Retriever()
    generator = Generator()

    question = input("Enter a test question: ")
    chunks   = retriever.retrieve(question)
    result   = generator.generate(question, chunks)

    print("\nAnswer:", result["answer"])
    print("Is no-answer:", result["is_no_answer"])
    print("Chunks used:", len(result["used_chunks"]))
