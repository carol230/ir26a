from ast import literal_eval

import gradio as gr

from retrieval import buscar
from generation import generar


def formatear_evidencias(evidencias):
    partes = []
    for i, e in enumerate(evidencias, 1):
        cats = ", ".join(literal_eval(e["terms"]))
        snippet = e["abstract"][:250].rsplit(" ", 1)[0] + "..."
        partes.append(
            f"**[{i}] {e['title']}**  \n"
            f"*{cats}* · score {e['score']:.2f}  \n"
            f"{snippet}"
        )
    return "\n\n".join(partes)


def responder_chat(mensaje, historial, top_k, usar_rerank):
    # cada consulta es independiente, no uso el historial para el retrieval
    try:
        evidencias = buscar(mensaje, top_k=int(top_k), rerank=usar_rerank)
    except Exception as e:
        return f"Ocurrió un error buscando en el índice: {e}"

    if not evidencias:
        return "No encontré resultados en el corpus para esa consulta."

    try:
        respuesta = generar(mensaje, evidencias)
    except Exception as e:
        return f"Ocurrió un error llamando a Gemini: {e}"

    return respuesta + "\n\n---\n**Evidence used:**\n\n" + formatear_evidencias(evidencias)


# controles extra: cuantas evidencias usar y si aplicar el re-ranking
slider_k = gr.Slider(1, 10, value=5, step=1, label="Evidencias (top-k)")
toggle_rerank = gr.Checkbox(value=True, label="Usar re-ranking (cross-encoder)")

demo = gr.ChatInterface(
    fn=responder_chat,
    type="messages",
    title="📚 arXiv RAG — ICCD753",
    description=(
        "Ask (in English) about machine learning / AI research. The system retrieves from "
        "~39k arXiv abstracts (mpnet + ChromaDB), re-ranks with a cross-encoder and answers "
        "with Gemini, citing the papers it used."
    ),
    additional_inputs=[slider_k, toggle_rerank],
    examples=[
        ["What are the main applications of Graph Neural Networks?", 5, True],
        ["How is reinforcement learning used in robotics?", 5, True],
        ["Recent advances in diffusion models for image generation", 5, True],
    ],
)

if __name__ == "__main__":
    demo.launch()
