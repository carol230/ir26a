import os

from google import genai

from config import GEMINI_MODEL, PROMPT_TEMPLATE

# la api key viene de una variable de entorno (en el space es un repository secret)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def generar(query, evidencias):
    contexto = "\n\n".join(
        f"[{i+1}] {e['title']}\n{e['abstract']}" for i, e in enumerate(evidencias)
    )
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, query=query)
    resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return resp.text
