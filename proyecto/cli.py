import os
import re
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import faiss

print("Cargando corpus...")
ruta_train = os.path.join(os.path.dirname(__file__), 'dataset', 'ModApte_train.csv')
df_reuters = pd.read_csv(ruta_train)

df = pd.DataFrame({
    'id_doc': df_reuters['new_id'],
    'raw': df_reuters['title'].fillna('') + ' ' + df_reuters['text'].fillna('')
})

STOPWORDS = set(stopwords.words('english'))
stemmer = SnowballStemmer('english')

def limpiar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-z\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def tokenizar(texto, stopwords=STOPWORDS):
    texto_limpio = limpiar_texto(texto)
    tokens = texto_limpio.split()
    tokens = [t for t in tokens if t not in stopwords and len(t) > 2]
    return tokens

def procesar(texto):
    if not isinstance(texto, str):
        return ""
    tokens = tokenizar(texto)
    stems = [stemmer.stem(t) for t in tokens]
    return " ".join(stems)

print("Preprocesando documentos...")
df['processed'] = df['raw'].apply(procesar)

print("Construyendo índices...")

vectorizador_binario = CountVectorizer(binary=True, lowercase=False)
matriz_binaria = vectorizador_binario.fit_transform(df['processed'])

vectorizador = TfidfVectorizer(lowercase=False)
tfidf_matrix = vectorizador.fit_transform(df['processed'])

corpus_para_bm25 = [doc.split() for doc in df['processed']]
bm25 = BM25Okapi(corpus_para_bm25)

print("Generando embeddings (puede tardar unos minutos)...")
modelo = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = modelo.encode(df['raw'].tolist(), show_progress_bar=True).astype('float32')
faiss.normalize_L2(embeddings)
indice_faiss = faiss.IndexFlatIP(embeddings.shape[1])
indice_faiss.add(embeddings)

print(f"Listo. {len(df)} documentos indexados.\n")

def recuperar_jaccard(query, top_n=10):
    query_p = procesar(query)
    query_vector = vectorizador_binario.transform([query_p])
    interseccion = matriz_binaria.dot(query_vector.T).toarray().flatten()
    terminos_por_doc = matriz_binaria.getnnz(axis=1)
    terminos_query   = query_vector.nnz
    union = terminos_por_doc + terminos_query - interseccion
    similitudes = np.where(union > 0, interseccion / union, 0.0)
    indices_mejores = similitudes.argsort()[-top_n:][::-1]
    resultados = df.iloc[indices_mejores].copy()
    resultados['score_jaccard'] = similitudes[indices_mejores]
    return resultados[['raw', 'score_jaccard']]

def recuperar_tfidf(query, top_n=10):
    query_p = procesar(query)
    query_vector = vectorizador.transform([query_p])
    similitudes = cosine_similarity(tfidf_matrix, query_vector).flatten()
    indices_mejores = similitudes.argsort()[-top_n:][::-1]
    resultados = df.iloc[indices_mejores].copy()
    resultados['score_similitud'] = similitudes[indices_mejores]
    return resultados[['raw', 'score_similitud']]

def recuperar_bm25(query, top_n=10):
    query_tokens = procesar(query).split()
    puntajes = bm25.get_scores(query_tokens)
    indices_mejores = puntajes.argsort()[-top_n:][::-1]
    resultados = df.iloc[indices_mejores].copy()
    resultados['score_bm25'] = puntajes[indices_mejores]
    return resultados[['raw', 'score_bm25']]

def recuperar_semantico(query, top_n=10):
    query_vector = modelo.encode([query]).astype('float32')
    faiss.normalize_L2(query_vector)
    distancias, indices = indice_faiss.search(query_vector, top_n)
    resultados = df.iloc[indices[0]].copy()
    resultados['score_semantico'] = distancias[0]
    return resultados[['raw', 'score_semantico']]

MODELOS = {
    '1': ('Jaccard',   recuperar_jaccard),
    '2': ('TF-IDF',    recuperar_tfidf),
    '3': ('BM25',      recuperar_bm25),
    '4': ('Semántico', recuperar_semantico),
}

def mostrar_resultados(resultados):
    score_col = [c for c in resultados.columns if c.startswith('score')][0]
    for i, (_, fila) in enumerate(resultados.iterrows(), 1):
        titulo = fila['raw'][:80].replace('\n', ' ')
        print(f"  {i}. [{fila[score_col]:.4f}]  {titulo}...")

def main():
    print("=" * 50)
    print("  Sistema de Recuperación de Información")
    print("=" * 50)

    modelo_actual = None
    fn_actual = None

    while True:
        if modelo_actual is None:
            print("\nModelos disponibles:")
            for k, (nombre, _) in MODELOS.items():
                print(f"  {k}. {nombre}")
            print("  q. Salir")

            opcion = input("\nElige un modelo: ").strip()

            if opcion == 'q':
                print("Hasta luego.")
                break
            if opcion not in MODELOS:
                print("Opción no válida.")
                continue

            modelo_actual, fn_actual = MODELOS[opcion]
            print(f"\nModelo activo: {modelo_actual}  (escribe 'modelo' para cambiar, 'salir' para salir)\n")

        query = input(f"[{modelo_actual}] Query: ").strip()

        if query == 'salir':
            print("Hasta luego.")
            break
        if query == 'modelo':
            modelo_actual = None
            continue
        if not query:
            continue

        resultados = fn_actual(query, top_n=5)
        print(f"\nTop 5 resultados:\n")
        mostrar_resultados(resultados)
        print()

if __name__ == '__main__':
    main()
