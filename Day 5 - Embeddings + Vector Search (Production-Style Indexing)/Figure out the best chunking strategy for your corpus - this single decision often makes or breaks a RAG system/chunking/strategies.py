import re


def fixed_size_chunker(text,chunk_size=512):

    words = text.split()

    chunks = []

    for i in range(0,len(words),chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))

    return chunks


def sentence_aware_chunker(text,max_words=512):

    sentences = re.split(r'(?<=[.!?])\s+',text)

    chunks = []

    current_chunk = []

    current_words = 0

    for sentence in sentences:

        count = len(sentence.split())

        if (current_words + count> max_words):

            chunks.append(" ".join(current_chunk))

            current_chunk = []
            current_words = 0

        current_chunk.append(sentence)

        current_words += count

    if current_chunk:

        chunks.append(" ".join(current_chunk))

    return chunks


def semantic_chunker(text):

    chunks = re.split(
        r"\n[A-Z][A-Za-z0-9\s]{3,}\n",
        text
    )

    return [
        chunk.strip()
        for chunk in chunks
        if chunk.strip()
    ]