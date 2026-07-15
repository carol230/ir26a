---
title: ArXiv RAG - ICCD753
emoji: 📚
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "5.49.1"
app_file: app.py
pinned: false
---

# arXiv RAG — Examen Final ICCD753

Sistema RAG (Retrieval-Augmented Generation) que responde preguntas sobre investigación en ML/AI usando ~39k abstracts de arXiv (dataset [arxiv-paper-abstracts](https://www.kaggle.com/datasets/spsayakpaul/arxiv-paper-abstracts) de Kaggle).

**Pipeline:** embeddings `all-mpnet-base-v2` (768d) → ChromaDB persistente (coseno) → retrieval denso top-20 → re-ranking con `cross-encoder/ms-marco-MiniLM-L-6-v2` → top-5 → Gemini 2.5 Flash genera la respuesta citando los papers.

## Estructura

- `app.py` — interfaz de chat (Gradio `ChatInterface`)
- `retrieval.py` — búsqueda vectorial + re-ranking
- `generation.py` — prompt + llamada a Gemini
- `config.py` — constantes del sistema y prompt template
- `chroma_db/` — índice vectorial precomputado (38,972 papers)
- `examen_final.ipynb` — notebook con el pipeline completo y la evaluación (secciones A–I)

## Ejecutar en local

```
pip install -r requirements.txt
```

Definir la variable de entorno `GEMINI_API_KEY` (la key **no** está en el código) y correr:

```
python app.py
```

La app queda en `http://localhost:7860`. Requiere la carpeta `chroma_db/` (la genera el notebook, secciones A–C).

## Deploy

Hugging Face Spaces (SDK Gradio, tier gratuito CPU). La API key de Gemini va en *Settings → Repository secrets* como `GEMINI_API_KEY`, y `chroma_db/` se sube al repo del Space para que la app arranque sin re-indexar.

**URL del Space:** https://huggingface.co/spaces/elmo2004/IvonneAyalaExamen

**App en vivo:** https://elmo2004-ivonneayalaexamen.hf.space
