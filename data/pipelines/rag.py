"""
Pipeline de Recuperación y Generación RAG (Retrieval-Augmented Generation)
Nexova Solutions — Monorepo
Responsabilidades:
1. retrieve(): Búsqueda semántica en Qdrant con filtro de similitud estricto (min_score).
2. generate_answer(): Síntesis con voz corporativa de Nexova y cláusula anti-alucinaciones.
3. query(): Función pública orquestadora (retrieve + generate_answer).
"""
import logging
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from qdrant_client import QdrantClient

# Aseguramos que la raíz del monorepo esté en sys.path
_ROOT_DIR = Path(__file__).resolve().parents[2]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

# Reutilizamos la función de embeddings optimizada de data/process/rag.py
from data.process.rag import embed

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nexova.rag.pipeline")

#configuración del entorno
DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DEFAULT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "nexova_knowledge")
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

def retrieve(
    query: str,
    *,
    k: int = 5,
    min_score: float=0.70,
    collection_name: str= DEFAULT_COLLECTION_NAME,
    qdrant_url: str = DEFAULT_QDRANT_URL,
) -> list[dict[str, Any]]:
    """
    Recupera los k fragmentos más relevantes de Qdrant que superen el umbral min_score.
    Args:
        query: Pregunta o término de búsqueda en lenguaje natural.
        k: Número máximo de fragmentos a recuperar (Top-K).
        min_score: Umbral de similitud coseno mínimo (evita alucinaciones).
        collection_name: Nombre de la colección en Qdrant.
        qdrant_url: URL del servicio Qdrant.
    Returns:
        Lista de diccionarios con el payload y el score de cada fragmento.
    """
    clean_query = query.strip()
    if not clean_query:
        return []
    
    client = QdrantClient(url=qdrant_url)
    query_vector = embed(clean_query)

    search_result = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=k,
        score_threshold=min_score,
    )

    clean_results: list[dict[str, Any]] = []
    for point in search_result.points:
        payload = dict(point.payload or {})
        payload["score"] = round(float(point.score), 4)
        clean_results.append(payload)

    logger.info(f"retrieve(): '{clean_query[:40]}...' -> {len(clean_results)} fragmentos sobre umbral {min_score}.")
    return clean_results

def generate_answer(question: str, context: list[dict[str, Any]]) -> str:
    """
    Genera una respuesta fundamentada exclusivamente en los fragmentos de contexto.
    Args:
        question: Pregunta del usuario.
        context: Fragmentos recuperados por retrieve(). 
    Returns:
        Respuesta generada o mensaje de rechazo honesto si no hay contexto.
    """
    # Cláusula anti-alucinaciones: sin contexto, respuesta honesta inmediata
    if not context:
        return "Lo siento, la documentación corporativa actual de Nexova Solutions no contiene información sobre esa consulta."
    # Ensamblar contexto con trazabilidad de documentos y secciones
    formatted_context = "\n\n---\n\n".join(
        f"Documento: {c.get('source_document', 'Doc')}\n"
        f"Sección: {c.get('section', 'General')}\n"
        f"Contenido:\n{c.get('text', '')}"
        for c in context
    )
    # Si hay API Key configurada, llamamos al LLM
    if LLM_API_KEY:
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {LLM_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": LLM_MODEL,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {
                                "role": "user",
                                "content": f"Contexto Oficial de Nexova:\n{formatted_context}\n\nPregunta: {question}",
                            },
                        ],
                        "temperature": 0.1,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.warning(f"Error al conectar con LLM ({exc}). Aplicando síntesis documental de respaldo.")
    # Fallback documental cuando no hay API Key o para entornos de test
    primary = context[0]
    return (
        f"[Respuesta fundamentada en {primary.get('source_document')} — Sección: {primary.get('section')}]:\n"
        f"{primary.get('text')}"
    )


def query(
    question: str,
    *,
    k: int = 5,
    min_score: float = 0.70,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    qdrant_url: str = DEFAULT_QDRANT_URL,
) -> str:
    """
    Punto de entrada orquestador del sistema RAG.
    
    1. Recupera los fragmentos semánticamente relevantes con score >= min_score.
    2. Genera una respuesta veraz y fundamentada con la voz de Nexova Solutions.
    
    Args:
        question: Pregunta del usuario.
        k: Número máximo de fragmentos a recuperar.
        min_score: Umbral de corte de similitud coseno.
        collection_name: Nombre de la colección en Qdrant.
        qdrant_url: URL del servidor Qdrant.
        
    Returns:
        Respuesta generada o mensaje de rechazo honesto si no hay información.
    """
    logger.info(f"query(): Procesando consulta: '{question}'")
    context = retrieve(
        question,
        k=k,
        min_score=min_score,
        collection_name=collection_name,
        qdrant_url=qdrant_url,
    )
    answer = generate_answer(question, context)
    return answer


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 PRUEBA 1: Consulta oficial de negocio")
    q1 = "¿Cuál es la garantía de reposición en headhunting?"
    print(f"Pregunta: {q1}\n")
    print(query(q1))

    print("\n" + "=" * 60)
    print("🧪 PRUEBA 2: Consulta fuera de dominio (Anti-alucinaciones)")
    q2 = "¿Cómo preparar una paella valenciana tradicional?"
    print(f"Pregunta: {q2}\n")
    print(query(q2))
    print("=" * 60 + "\n")