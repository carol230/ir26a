# Informe Técnico — Sistema de Recuperación de Información
**Recuperación de Información — Prof. Iván Carrera**  
Carolina Ayala · Mayo 2026

---

## 1. Descripción del corpus

El corpus que se usó es **Reuters-21578**, específicamente el split **ModApte** de entrenamiento. Contiene artículos de noticias financieras en inglés publicados por Reuters en 1987, cada uno con título, cuerpo de texto, y topics asignados manualmente (por ejemplo `cocoa`, `wheat`, `crude`, `earn`).

El split de entrenamiento tiene **9,603 documentos**. Para indexarlos se concatenó el título con el cuerpo, porque el título resume el tema del artículo de forma muy directa y aporta señal útil para la recuperación.

Después del preprocesamiento, el vocabulario quedó en **24,038 términos únicos**. De esos, 12,133 aparecen en un solo documento, lo que es bastante normal en un corpus de noticias donde hay muchos nombres propios y términos muy específicos. Los términos más frecuentes son `reuter` (en 8,732 documentos), `said`, `mln` y `dlrs`, que son básicamente ruido de dominio: aparecen en casi todo porque son parte del formato de los despachos de Reuters.

---

## 2. Decisiones de diseño

### Preprocesamiento

El preprocesamiento sigue el mismo flujo que vimos en clase: lowercase, eliminación de caracteres no alfabéticos con regex, filtro de stopwords de NLTK (198 palabras en inglés), y stemming con SnowballStemmer.

Una decisión importante fue **no** aplicar este preprocesamiento para los embeddings. Sentence-transformers trabaja sobre lenguaje natural, y si le pasamos texto con stems (`reuter`, `compani`, `dlr`) el modelo pierde contexto semántico. Por eso el modelo semántico usa la columna `raw` directamente.

### Índice invertido

El índice tiene la forma `{término: {id_doc: frecuencia}}`. Se guardó la frecuencia porque TF-IDF y BM25 la necesitan para calcular los pesos, así que era mejor tenerla disponible desde el índice en lugar de tener que releer los documentos después.

### Los cuatro modelos

- **Jaccard** con vectores binarios: el modelo más simple. Mide qué tan parecidos son dos conjuntos de términos sin considerar cuántas veces aparece cada uno.
- **TF-IDF** con similitud coseno: tiene en cuenta la frecuencia de los términos pero penaliza los que aparecen en muchos documentos. Normaliza por la longitud del documento.
- **BM25**: similar a TF-IDF pero satura la frecuencia (un término que aparece 100 veces no vale 10 veces más que uno que aparece 10 veces) y penaliza documentos más largos que el promedio.
- **Semántico** con `all-MiniLM-L6-v2` y FAISS: genera vectores de 384 dimensiones que capturan significado, no solo palabras exactas. Se almacenan normalizados en un índice FAISS `IndexFlatIP`, lo que equivale a similitud coseno.

---

## 3. Ejemplos de consultas y resultados

Se probaron tres queries representativas del dominio del corpus.

### "cocoa trade"

| Modelo    | Documento top-1                                              | Score  |
|-----------|--------------------------------------------------------------|--------|
| Jaccard   | YEUTTER SAYS U.S. SHOULD STRESS TRADE NEGOTIATIONS...        | 0.1250 |
| TF-IDF    | ICCO COUNCIL AGREES COCOA BUFFER STOCK...                    | 0.6110 |
| BM25      | COCOA COUNCIL MEETING ENDS AFTER AGREEING...                 | 12.14  |
| Semántico | COCOA COUNCIL MEETING ENDS AFTER AGREEING...                 | 0.5967 |

Jaccard recupera un artículo sobre negociaciones comerciales que contiene la palabra "trade", pero no habla específicamente de cacao. Los otros tres modelos recuperan documentos del Consejo Internacional del Cacao, que es exactamente el tipo de contenido relevante. BM25 y el semántico coinciden en el top-1.

### "wheat grain prices"

| Modelo    | Documento top-1                                              | Score  |
|-----------|--------------------------------------------------------------|--------|
| Jaccard   | IWC lifts 1986/87 world wheat, coarse grain estimate...      | 0.1667 |
| TF-IDF    | WORLD GRAIN TRADE RECOVERY MAY BE UNDERWAY...                | 0.4767 |
| BM25      | WORLD GRAIN TRADE RECOVERY MAY BE UNDERWAY...                | 15.49  |
| Semántico | SMALL QUANTITY OF UK WHEAT SOLD TO HOME...                   | 0.6431 |

TF-IDF y BM25 coinciden en el top-1. Jaccard también recupera un documento relevante aunque no sea el mismo. El semántico recupera algo diferente pero igualmente pertinente: una noticia sobre ventas de trigo en el mercado doméstico del Reino Unido.

### "oil barrel"

| Modelo    | Documento top-1                                              | Score  |
|-----------|--------------------------------------------------------------|--------|
| Jaccard   | CONOCO RAISES CRUDE OIL PRICES UP TO ONE DLR BARREL...       | 0.2000 |
| TF-IDF    | EIA SAYS DISTILLATE, GAS STOCKS OFF IN WEEK...               | 0.5508 |
| BM25      | HAMILTON OIL SAYS RESERVES RISE...                           | 11.97  |
| Semántico | STUDY GROUP URGES INCREASED U.S. OIL RESERVES...             | 0.4576 |

Esta query es la más interesante porque los cuatro modelos recuperan documentos distintos. Jaccard recupera el más literal: un artículo que contiene "oil" y "barrel" exactamente. TF-IDF y BM25 recuperan documentos relacionados con petróleo pero que no usan la palabra "barrel". El semántico recupera algo sobre reservas de petróleo, que es conceptualmente relacionado aunque comparta muy pocos términos con la query.

---

## 4. Evaluación

Para la evaluación se definieron 5 queries con ground truth basado en los topics de Reuters. Los documentos relevantes para cada query son todos los del corpus que tienen ese topic asignado.

| Query   | Docs relevantes |
|---------|-----------------|
| cocoa   | 55              |
| wheat   | 212             |
| crude   | 389             |
| earn    | 2,877           |
| trade   | 369             |

Se calcularon precisión y recall a k=10, y Average Precision (AP) por query. El MAP es el promedio de los AP sobre las 5 queries.

### Resultados por modelo

**Jaccard**

| query  | precision | recall | AP     |
|--------|-----------|--------|--------|
| cocoa  | 1.0000    | 0.1818 | 0.1818 |
| wheat  | 0.9000    | 0.0425 | 0.0402 |
| crude  | 1.0000    | 0.0257 | 0.0257 |
| earn   | 0.8000    | 0.0028 | 0.0022 |
| trade  | 0.6000    | 0.0163 | 0.0120 |
| **MAP** | | | **0.0524** |

**TF-IDF**

| query  | precision | recall | AP     |
|--------|-----------|--------|--------|
| cocoa  | 1.0000    | 0.1818 | 0.1818 |
| wheat  | 1.0000    | 0.0472 | 0.0472 |
| crude  | 1.0000    | 0.0257 | 0.0257 |
| earn   | 0.9000    | 0.0031 | 0.0025 |
| trade  | 0.9000    | 0.0244 | 0.0205 |
| **MAP** | | | **0.0555** |

**BM25**

| query  | precision | recall | AP     |
|--------|-----------|--------|--------|
| cocoa  | 1.0000    | 0.1818 | 0.1818 |
| wheat  | 1.0000    | 0.0472 | 0.0472 |
| crude  | 1.0000    | 0.0257 | 0.0257 |
| earn   | 0.9000    | 0.0031 | 0.0025 |
| trade  | 0.9000    | 0.0244 | 0.0231 |
| **MAP** | | | **0.0560** |

**Semántico**

| query  | precision | recall | AP     |
|--------|-----------|--------|--------|
| cocoa  | 1.0000    | 0.1818 | 0.1818 |
| wheat  | 1.0000    | 0.0472 | 0.0472 |
| crude  | 0.9000    | 0.0231 | 0.0223 |
| earn   | 1.0000    | 0.0035 | 0.0035 |
| trade  | 0.6000    | 0.0163 | 0.0099 |
| **MAP** | | | **0.0529** |

### Resumen MAP

| Modelo    | MAP    |
|-----------|--------|
| BM25      | 0.0560 |
| TF-IDF    | 0.0555 |
| Semántico | 0.0529 |
| Jaccard   | 0.0524 |

### Análisis

Lo primero que llama la atención es que todos los MAP son muy bajos (alrededor de 0.05). Esto no significa que los modelos sean malos, sino que la métrica se ve afectada directamente por el tamaño del conjunto relevante. Con k=10 y 2,877 documentos relevantes para `earn`, el recall máximo posible es 10/2877 = 0.35%, lo que arrastra el AP de esa query hacia casi cero para todos los modelos. Si se evaluara con k=100 o k=1000 los números serían muy distintos.

Con eso en mente, hay algunas observaciones interesantes:

**BM25 gana, pero por muy poco.** La diferencia entre BM25 (0.0560) y TF-IDF (0.0555) es de 0.0005, que es prácticamente insignificante con solo 5 queries. La ventaja de BM25 se ve más claramente en la query `trade`, donde AP = 0.0231 vs 0.0205 de TF-IDF. Eso sugiere que en documentos de longitud variable como los de Reuters, la normalización por longitud de BM25 ayuda un poco.

**El modelo semántico no supera a BM25 ni a TF-IDF.** Esto puede parecer sorprendente, pero tiene sentido en este corpus. Reuters usa terminología muy consistente: cuando un artículo es sobre trigo, usa la palabra "wheat". No hay mucha variación de vocabulario que aprovechar. El semántico brilla cuando hay paráfrasis o sinónimos, pero en un corpus de noticias financieras con términos muy estandarizados, BM25 es suficiente. Además, el semántico tiene un comportamiento peor en `trade` (AP = 0.0099 vs 0.0231 de BM25), probablemente porque "trade" como concepto semántico se solapa con muchos artículos que no tienen el topic `trade` asignado.

**Jaccard tiene la precisión más baja en `trade` (0.6)**, lo que confirma que ignorar la frecuencia de los términos es una limitación real. Un documento que menciona "trade" una sola vez en un contexto diferente puede quedar con el mismo score que un artículo completamente sobre comercio internacional.

**La query `cocoa` es la más fácil para todos los modelos.** Con solo 55 documentos relevantes, top-10 captura el 18% de ellos, y la precisión es perfecta (1.0) en todos los modelos. Cuando el conjunto relevante es pequeño y el vocabulario es específico, todos los modelos funcionan igual de bien.

En resumen, para este corpus BM25 es el mejor modelo dado que combina buen desempeño con una implementación sencilla. El modelo semántico sería más útil en un corpus con mayor variación de vocabulario, como artículos de Wikipedia o preguntas en lenguaje natural.
