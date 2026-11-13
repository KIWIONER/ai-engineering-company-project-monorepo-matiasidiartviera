"""
Router de Consulta a la Base de Conocimiento RAG (Nexova Solutions).
Endpoint REST protegido con Auth Guard Standard para consumo de frontend y agentes.
"""
from __future__ import annotations
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from data.pipelines.rag import generate_answer, retrieve
from services.api.routes.auth import get_current_user

logger = logging.getLogger("nexova.knowledge_route")

router = APIRouter(tags=["Knowledge base (RAG)"])

#Modelos Pydantic de Validación de Entrada y salida.
class KnowledgeQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Pregunta en lenguaje natural sobre políticas, SLAs o catálogo de Nexova.",
        examples= ["¿Cuál es la política de resposición en procesos de headhunting?"],
    )
    k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Número máximo de fragmentos semánticos a recuperar.",
    )
    min_score: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Umbral de similitud coseno mínimo.",
    )

class SourceChunk(BaseModel):
    source_document: str = Field(description="Nombre del documento fuente")
    document_title: str = Field(description="Título general del documento")
    section: str = Field(description="Sección de procedencia")
    score: float = Field(description="Puntuación de similitud coseno")
    text: str = Field(description="Texto del fragmento")

class KnowledgeQueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceChunk]
    sources_count: int

@router.post(
    "/knowledge/query",
    response_model=KnowledgeQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar la base de conocimiento corporativa de Nexova",
    description="""Endpoint protegido que ejecuta búsqueda semántica en 
    Qdrant y síntesis con voz de Nexova""",
)

@router.post(
    "/api/knowledge/query",
    response_model=KnowledgeQueryResponse,
    include_in_schema=False,
)
def query_knowledge_base(
    payload: KnowledgeQueryRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> KnowledgeQueryResponse:
    """
    Ejecuta el pipeline RAG completo para un usuario autenticado:
    1. Recuperación en Qdrant con filtro por umbral (min_score).
    2. Síntesis generativa garantizando veracidad y honestidad.
    3. Retorno estructurado de la respuesta y las fuentes de evidencia.
    """
    logger.info(
        f"Usuario autenticado '{current_user.get('email', 'anon')}' consultando: '{payload.question}'"
    )

    try:
        # Recuperación vectorial con umbral calibrado
        sources = retrieve(
            query=payload.question,
            k=payload.k,
            min_score=payload.min_score,
        )
        # Generación condicionada al contexto
        answer = generate_answer(
            question=payload.question,
            context=sources,
        )
        clean_sources = [
            SourceChunk(
                source_document=str(s.get("source_document", "Desconocido")),
                document_title=str(s.get("document_title", "Documento")),
                section=str(s.get("section", "General")),
                score=float(s.get("score", 0.0)),
                text=str(s.get("text", "")),
            )
            for s in sources
        ]
        return KnowledgeQueryResponse(
            question=payload.question,
            answer=answer,
            sources=clean_sources,
            sources_count=len(clean_sources),
        )
    except Exception as exc:
        logger.error(f"Error procesando consulta RAG: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al consultar la base de conocimiento: {str(exc)}",
        )