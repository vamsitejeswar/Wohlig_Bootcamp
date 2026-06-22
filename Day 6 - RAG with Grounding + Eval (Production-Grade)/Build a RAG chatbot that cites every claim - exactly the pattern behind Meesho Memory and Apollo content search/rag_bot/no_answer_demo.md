# No-Answer Demo — 5 Out-of-Corpus Questions

These 5 questions are about topics that do NOT exist in our document corpus
(doc1.pdf – doc10.pdf). The bot should respond with:
> "I couldn't find this information in the provided documents."

---

## Question 1
**"What is the recipe for making chocolate cake?"**

Expected response:
> I couldn't find this information in the provided documents.

Screenshot: `screenshots/no_answer_1.png`

---

## Question 2
**"Who won the FIFA World Cup in 2022 and what was the final score?"**

Expected response:
> I couldn't find this information in the provided documents.

Screenshot: `screenshots/no_answer_2.png`

---

## Question 3
**"What are the lyrics to Bohemian Rhapsody by Queen?"**

Expected response:
> I couldn't find this information in the provided documents.

Screenshot: `screenshots/no_answer_3.png`

---

## Question 4
**"How many moons does Jupiter have?"**

Expected response:
> I couldn't find this information in the provided documents.

Screenshot: `screenshots/no_answer_4.png`

---

## Question 5
**"Give me a Python code to build a REST API using FastAPI."**

Expected response:
> I couldn't find this information in the provided documents.

Screenshot: `screenshots/no_answer_5.png`

---

## Why this matters

A regular LLM would confidently answer all 5 questions above from its
training data — that's hallucination in a RAG context.

Our grounding prompt forces Gemini to:
1. Only use the retrieved context chunks
2. Say "I don't know" when no relevant chunk is found
3. Never fabricate an answer

This is the key difference between a production RAG system and a naive
LLM wrapper.
