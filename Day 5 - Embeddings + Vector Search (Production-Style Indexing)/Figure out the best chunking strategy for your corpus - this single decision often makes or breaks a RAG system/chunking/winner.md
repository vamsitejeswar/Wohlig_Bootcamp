# Chunking Evaluation Results

## Aggregate Scores

| Strategy | Recall@5 | Recall@10 |
|-----------|-----------|-----------|
| Fixed Size | 68% | 76% |
| Sentence Aware | 64% | 76% |
| Semantic | 76% | 88% |

## Winner

Semantic Chunking

## Why Semantic Won

The PDF corpus contains structured content with sections and headings. Semantic chunking preserves related information within the same chunk and avoids breaking context across sections.

This resulted in the highest retrieval performance for both Recall@5 and Recall@10.

## Rule of Thumb

Use Fixed Size:
- OCR documents
- Unstructured text
- Fast prototyping

Use Sentence Aware:
- Articles
- Blogs
- Narrative content

Use Semantic:
- Reports
- Policies
- RBI Circulars
- Annual Reports
- Documents with clear headings and sections

## Conclusion

For this corpus, Semantic Chunking achieved the best retrieval quality with 76% Recall@5 and 88% Recall@10, making it the recommended chunking strategy for future RAG implementations.