"""
Tests unitarios aislados para el pipeline RAG y endpoint de conocimiento.
Utiliza mocks para ejecutarse en CI/CD sin depender de servicios externos ni Qdrant en vivo.
"""
import os
import sys
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from data.pipelines.rag import retrieve, generate_answer, query
from services.api.main import app
from services.api.security import create_access_token
from services.api.routes.auth import get_current_user


# ==========================================
# 1. Tests de Recuperación (retrieve)
# ==========================================

def test_retrieve_empty_query():
    """Una consulta vacía debe retornar una lista vacía sin llamar a Qdrant."""
    results = retrieve("   ")
    assert results == []


@patch("data.pipelines.rag.embed")
@patch("data.pipelines.rag.QdrantClient")
def test_retrieve_filters_by_min_score(mock_qdrant_class, mock_embed):
    """Verifica que retrieve() filtre puntos por debajo de min_score y limpie el payload."""
    mock_embed.return_value = [0.1] * 384
    mock_client = MagicMock()
    mock_qdrant_class.return_value = mock_client

    # Simular puntos retornados por Qdrant
    point_high = MagicMock()
    point_high.score = 0.85
    point_high.payload = {
        "source_document": "politicas_contratacion_seleccion.md",
        "section": "Garantía de Reposición",
        "text": "Garantía de 90 días naturales.",
    }

    mock_response = MagicMock()
    mock_response.points = [point_high]
    mock_client.query_points.return_value = mock_response

    results = retrieve("garantía de reposición", min_score=0.70)

    assert len(results) == 1
    assert results[0]["source_document"] == "politicas_contratacion_seleccion.md"
    assert results[0]["score"] == 0.85
    # Verificar que el cliente fue invocado con el umbral esperado
    mock_client.query_points.assert_called_once()
    assert mock_client.query_points.call_args.kwargs["score_threshold"] == 0.70


# ==========================================
# 2. Tests de Generación (generate_answer)
# ==========================================

def test_generate_answer_empty_context_triggers_refusal():
    """Si el contexto está vacío, debe responder con el rechazo anti-alucinaciones estándar."""
    answer = generate_answer("¿Cómo preparar paella?", context=[])
    assert "Lo siento, la documentación corporativa actual de Nexova Solutions no contiene información" in answer


def test_generate_answer_fallback_with_context():
    """Sin API key configurada, retorna la síntesis documental estructurada."""
    mock_context = [
        {
            "source_document": "slas_y_niveles_servicio.md",
            "section": "Matriz de Prioridad",
            "text": "P1 requiere respuesta en menos de 15 minutos.",
        }
    ]
    with patch("data.pipelines.rag.LLM_API_KEY", ""):
        answer = generate_answer("¿Cuál es el SLA de P1?", context=mock_context)
        assert "slas_y_niveles_servicio.md" in answer
        assert "P1 requiere respuesta en menos de 15 minutos." in answer

@patch("httpx.Client")
def test_generate_answer_with_llm_api_key(mock_client_class):
    """Con API key configurada, invoca al LLM pasando SYSTEM_PROMPT y retorna su síntesis."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Respuesta sintetizada por el LLM con la voz corporativa de Nexova."}}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_client.post.return_value = mock_response
    mock_context = [
        {
            "source_document": "politicas_contratacion_seleccion.md",
            "section": "Garantía de Reposición y Continuidad",
            "text": "Garantía de 90 días naturales.",
        }
    ]
    with patch("data.pipelines.rag.LLM_API_KEY", "sk-test-token-12345"):
        answer = generate_answer("¿Cuál es la garantía?", context=mock_context)
        assert answer == "Respuesta sintetizada por el LLM con la voz corporativa de Nexova."
        
        # Validar que se invocó al LLM pasando SYSTEM_PROMPT en el payload sin NameError
        mock_client.post.assert_called_once()
        payload_sent = mock_client.post.call_args.kwargs["json"]
        assert payload_sent["messages"][0]["role"] == "system"
        assert "Nexova Solutions" in payload_sent["messages"][0]["content"]
        
# ==========================================
# 3. Tests de Orquestación (query)
# ==========================================

@patch("data.pipelines.rag.retrieve")
@patch("data.pipelines.rag.generate_answer")
def test_query_orchestrator(mock_generate, mock_retrieve):
    """query() debe componer retrieve() y generate_answer() secuencialmente."""
    mock_retrieve.return_value = [{"text": "Contexto simulado"}]
    mock_generate.return_value = "Respuesta final sintetizada"

    res = query("¿Pregunta de prueba?", k=3, min_score=0.75)

    mock_retrieve.assert_called_once_with(
        "¿Pregunta de prueba?",
        k=3,
        min_score=0.75,
        collection_name="nexova_knowledge",
        qdrant_url="http://localhost:6333",
    )
    mock_generate.assert_called_once_with("¿Pregunta de prueba?", [{"text": "Contexto simulado"}])
    assert res == "Respuesta final sintetizada"


# ==========================================
# 4. Tests del Endpoint FastAPI (/knowledge/query)
# ==========================================

client = TestClient(app)


def test_knowledge_endpoint_unauthorized():
    """El endpoint debe bloquear peticiones sin token JWT con HTTP 401 (Auth Guard)."""
    response = client.post(
        "/knowledge/query",
        json={"question": "¿Cuál es la política de reposición?"},
    )
    assert response.status_code == 401


@patch("services.api.routes.knowledge.retrieve")
@patch("services.api.routes.knowledge.generate_answer")
def test_knowledge_endpoint_authenticated(mock_generate, mock_retrieve):
    """Con sesión autenticada válida, el endpoint procesa y devuelve la respuesta estructurada."""
    mock_retrieve.return_value = [
        {
            "source_document": "politicas_contratacion_seleccion.md",
            "document_title": "Políticas de Selección",
            "section": "Tarifas",
            "score": 0.88,
            "text": "18% del SBA para perfiles tech.",
        }
    ]
    mock_generate.return_value = "Los honorarios para perfiles tech son del 18% del SBA."
    # Usamos dependency_overrides de FastAPI para simular un usuario autenticado sin tocar la DB
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "admin-test-id",
        "email": "admin@nexova.com",
        "role": "admin",
    }
    try:
        response = client.post(
            "/knowledge/query",
            json={"question": "¿Cuáles son las tarifas?", "k": 3, "min_score": 0.70},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "¿Cuáles son las tarifas?"
        assert "18% del SBA" in data["answer"]
        assert data["sources_count"] == 1
        assert data["sources"][0]["source_document"] == "politicas_contratacion_seleccion.md"
        assert data["sources"][0]["score"] == 0.88
    finally:
        app.dependency_overrides.clear()