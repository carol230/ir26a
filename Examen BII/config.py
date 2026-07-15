# constantes del sistema RAG

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "arxiv_papers"

EMBEDDING_MODEL = "all-mpnet-base-v2"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GEMINI_MODEL = "gemini-2.5-flash"

TOP_K_RETRIEVAL = 20  # candidatos de la etapa densa
TOP_K_FINAL = 5       # lo que queda tras el re-ranking

PROMPT_TEMPLATE = """You are a research assistant that answers questions about machine learning and AI research.
Answer using ONLY the arXiv paper abstracts provided as context below.

Rules:
- Base your answer exclusively on the context. Do not use outside knowledge.
- Cite the papers you use with their bracketed number, like [1] or [3].
- If the context does not contain enough information to answer the question, reply exactly:
  "The corpus does not contain sufficient information to answer this question."

Context:
{contexto}

Question: {query}

Answer:"""
