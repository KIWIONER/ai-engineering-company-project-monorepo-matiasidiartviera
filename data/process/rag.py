"""
Módulo de Procesamiento e Ingesta de Conocimiento Vectorial (RAG)
Nexova Solutions — Monorepo

Responsabilidades:
1. Carga y parsing semántico de documentos corporativos en Markdown.
2. Generación de embeddings densos de 384 dimensiones con FastEmbed (ONNX local).
3. Creación/recreación idempotente e indexación en Qdrant.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nexova.rag.process")

# Configuración por defecto del sistema
DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DEFAULT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "nexova_knowledge")
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_DIMENSION = 384
CORPUS_DIR = Path(__file__).resolve().parents[2] / "docs" / "company-knowledge-base"

# Singleton para el modelo de embeddings (carga perezosa para optimizar memoria)
_embedding_model: TextEmbedding | None = None


def get_embedding_model() -> TextEmbedding:
    """Retorna la instancia única del modelo de embeddings."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Cargando modelo de embeddings local: {EMBEDDING_MODEL_NAME}...")
        _embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
    return _embedding_model


def embed(text: str) -> list[float]:
    """
    Convierte una cadena de texto en un vector denso de 384 dimensiones.
    
    Args:
        text: Texto a vectorizar.
        
    Returns:
        Lista de 384 floats representando el embedding normalizado.
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        return [0.0] * VECTOR_DIMENSION
    model = get_embedding_model()
    embeddings = list(model.embed([cleaned_text]))
    return embeddings[0].tolist()


def chunk_markdown(content: str, filename: str) -> list[dict[str, Any]]:
    """
    Segmenta un documento Markdown por encabezados de nivel 2 (##) para preservar
    unidades semánticas completas (políticas, SLAs, procedimientos).
    
    Args:
        content: Contenido completo del archivo Markdown.
        filename: Nombre del archivo de origen para trazabilidad.
        
    Returns:
        Lista de chunks con su respectivo texto y metadatos.
    """
    chunks: list[dict[str, Any]] = []

    # Extraer título del documento (# Título)
    doc_title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    doc_title = doc_title_match.group(1).strip() if doc_title_match else filename

    # Dividir por secciones '## '
    sections = re.split(r"(?m)(?=^##\s+)", content)
    chunk_index = 0

    for section in sections:
        section_text = section.strip()
        if not section_text:
            continue

        # Ignorar el encabezado de nivel 1 si quedó aislado al inicio
        if section_text.startswith("# ") and "\n## " not in section_text:
            continue

        # Extraer nombre de la sección
        section_match = re.match(r"^##\s+(.+)$", section_text, re.MULTILINE)
        section_name = section_match.group(1).strip() if section_match else "General"

        chunks.append({
            "source_document": filename,
            "document_title": doc_title,
            "section": section_name,
            "company": "Nexova Solutions",
            "language": "es",
            "chunk_index": chunk_index,
            "text": section_text,
        })
        chunk_index += 1

    return chunks


def setup(
    collection_name: str = DEFAULT_COLLECTION_NAME,
    qdrant_url: str = DEFAULT_QDRANT_URL,
    corpus_path: Path = CORPUS_DIR,
) -> dict[str, Any]:
    """
    Punto de entrada de inicialización e ingesta idempotente del sistema RAG.
    
    1. Recrea la colección en Qdrant (elimina versiones anteriores si existen).
    2. Lee y procesa todos los archivos .md en docs/company-knowledge-base/.
    3. Vectoriza cada sección e inserta los puntos con su payload en Qdrant.
    
    Returns:
        Diccionario con el resumen de la indexación.
    """
    logger.info(f"Conectando a Qdrant en {qdrant_url}...")
    client = QdrantClient(url=qdrant_url)

    logger.info(f"Recreando colección '{collection_name}' (dimensión: {VECTOR_DIMENSION}, métrica: Cosine)...")
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=VECTOR_DIMENSION,
            distance=models.Distance.COSINE,
        ),
    )

    if not corpus_path.exists():
        raise FileNotFoundError(f"El directorio del corpus no existe: {corpus_path}")

    md_files = sorted(list(corpus_path.glob("*.md")))
    if not md_files:
        raise ValueError(f"No se encontraron archivos Markdown en: {corpus_path}")

    all_chunks: list[dict[str, Any]] = []
    for file_path in md_files:
        content = file_path.read_text(encoding="utf-8")
        file_chunks = chunk_markdown(content, file_path.name)
        all_chunks.extend(file_chunks)
        logger.info(f"Documento '{file_path.name}': {len(file_chunks)} chunks semánticos generados.")

    logger.info(f"Vectorizando e indexando {len(all_chunks)} chunks en Qdrant...")
    points: list[models.PointStruct] = []

    for chunk in all_chunks:
        vector = embed(chunk["text"])
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk['source_document']}#{chunk['chunk_index']}"))
        
        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload=chunk,
            )
        )

    # Inserción en lote (batch upsert)
    client.upsert(collection_name=collection_name, points=points)

    collection_info = client.get_collection(collection_name=collection_name)
    logger.info(f"✅ Indexación completada: {collection_info.points_count} puntos almacenados en '{collection_name}'.")

    return {
        "status": "success",
        "collection_name": collection_name,
        "documents_indexed": len(md_files),
        "chunks_indexed": len(all_chunks),
        "points_count": collection_info.points_count,
    }


if __name__ == "__main__":
    summary = setup()
    print("\n--- RESUMEN DE INDEXACIÓN ---")
    for key, value in summary.items():
        print(f"  {key}: {value}")