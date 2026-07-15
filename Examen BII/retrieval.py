import os
os.environ["USE_TF"] = "0"  # evita que transformers intente importar tensorflow

import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder

from config import (CHROMA_PATH, COLLECTION_NAME, EMBEDDING_MODEL,
                    CROSS_ENCODER_MODEL, TOP_K_RETRIEVAL, TOP_K_FINAL)

# todo lo pesado se carga una sola vez al importar el modulo
model = SentenceTransformer(EMBEDDING_MODEL)
reranker = CrossEncoder(CROSS_ENCODER_MODEL)
col = chromadb.PersistentClient(path=CHROMA_PATH).get_collection(COLLECTION_NAME)


def buscar(query, top_k=TOP_K_FINAL, rerank=True):
    q_emb = model.encode(query, normalize_embeddings=True)
    res = col.query(query_embeddings=[q_emb.tolist()], n_results=TOP_K_RETRIEVAL)

    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]

    if rerank:
        # re-ranking: el cross-encoder puntua cada par (query, documento)
        scores = reranker.predict([(query, d) for d in docs])
        orden = scores.argsort()[::-1][:top_k]
        get_score = lambda i: float(scores[i])
    else:
        # sin re-ranking me quedo con el orden del retrieval denso (similitud coseno)
        orden = range(min(top_k, len(docs)))
        get_score = lambda i: round(1 - dists[i], 3)

    return [
        {"title": metas[i]["title"],
         "terms": metas[i]["terms"],
         # el documento guardado es titulo+abstract, me quedo solo con el abstract
         "abstract": docs[i][len(metas[i]["title"]):].strip(),
         "score": get_score(i)}
        for i in orden
    ]
