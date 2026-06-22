"""
app.py - Simple RAG Chatbot with Citations
"""
import os
import logging

# Must be set BEFORE importing gradio so the cache lands in this folder
os.environ["GRADIO_TEMP_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gradio")

import gradio as gr
from retriever import Retriever, RetrievedChunk
from generator import Generator, NO_ANSWER_PHRASE
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize once at startup
retriever = Retriever()
generator = Generator()


def format_sources(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "_No relevant chunks retrieved._"
    lines = ["**Retrieved Sources:**"]
    for c in chunks:
        lines.append(f"- `{c.doc_id}` · page {c.page} · score {c.score:.3f}")
    return "\n".join(lines)


def chat(question: str, history: list):
    """
    Takes the user question + chat history,
    returns updated history + sources panel text.
    """
    if not question.strip():
        return list(history or []), "_Ask a question to see sources._"

    try:
        chunks = retriever.retrieve(question)
        result = generator.generate(question, chunks)
        answer = result["answer"]
        sources_md = format_sources(result["used_chunks"])
        # Prefix with warning if bot said it doesn't know
        if result["is_no_answer"]:
            display_answer = f"⚠️ {answer}"
        else:
            display_answer = answer
    except Exception as e:
        logger.exception(e)
        display_answer = f"Error: {e}"
        sources_md = "_Error during retrieval._"

    history = list(history or [])
    history.append({"role": "user",      "content": question})
    history.append({"role": "assistant", "content": display_answer})
    return history, sources_md


# ── UI ────────────────────────────────────────────────────────────────────────

with gr.Blocks(title="RAG Chatbot with Citations") as demo:

    gr.Markdown("# RAG Chatbot with Citations")
    gr.Markdown(
        "Ask questions about the documents. "
        "Every answer cites its source as `[doc_id:page]`. "
        "If the answer is not in the documents the bot says so — it never guesses."
    )

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Conversation", height=480)
            question_box = gr.Textbox(
                placeholder="Ask a question...",
                label="Your Question",
                lines=2,
            )
            with gr.Row():
                submit_btn = gr.Button("Ask", variant="primary")
                clear_btn  = gr.Button("Clear")

        with gr.Column(scale=2):
            gr.Markdown("### Retrieved Sources")
            sources_box = gr.Markdown("_Sources will appear here._")

    # 5 example questions — 3 in-corpus, 2 out-of-corpus (should say I don't know)
    gr.Examples(
        examples=[
            ["What is the Föllmer process?"],
            ["What is Wasserstein distance used for in DDPMs?"],
            ["What is the main contribution of the Oxford paper on wide neural networks?"],
            ["What is the recipe for making chocolate cake?"],
            ["Who won the FIFA World Cup in 2022?"],
        ],
        inputs=question_box,
    )

    submit_btn.click(
        fn=chat,
        inputs=[question_box, chatbot],
        outputs=[chatbot, sources_box],
    ).then(fn=lambda: "", outputs=question_box)

    question_box.submit(
        fn=chat,
        inputs=[question_box, chatbot],
        outputs=[chatbot, sources_box],
    ).then(fn=lambda: "", outputs=question_box)

    clear_btn.click(
        fn=lambda: ([], "_Sources will appear here._"),
        outputs=[chatbot, sources_box],
    )


if __name__ == "__main__":
    demo.launch(share=True)
