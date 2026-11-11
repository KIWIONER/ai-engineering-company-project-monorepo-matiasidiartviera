"""
tests/pipelines/test_agent_evals.py
Suite de evaluación (evals) para el agente de soporte con LangGraph.
Verifica:
1. Enrutamiento del trace ante preguntas vacías.
2. Orden estricto de ejecución: retrieve antes que generate_answer.
3. Rechazo honesto ante ausencia de contexto sobre el umbral.
4. Anclaje de la respuesta en la base documental oficial (company-BRIEFING.md).
5. Persistencia e inspección mediante checkpointing.
"""
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from unittest.mock import patch
from langgraph.checkpoint.memory import MemorySaver
from services.agent.graph import create_agent_graph
from fastapi.testclient import TestClient
from services.api.main import app
from services.api.routes.auth import get_current_user

def test_eval_1_empty_question_routing_and_trace():
    """
    Eval 1: Pregunta vacía debe enrutar a rechazo honesto directamente,
    sin ejecutar retrieve ni generate_answer.
    """
    checkpointer = MemorySaver()
    app = create_agent_graph(checkpointer=checkpointer)
    thread_config = {"configurable": {"thread_id": "eval-empty-q"}}
    state = app.invoke(
        {
            "question": "   ",
            "context": [],
            "answer": "",
            "error": None,
            "execution_trace": [],
        },
        config=thread_config,
    )
    trace = state["execution_trace"]
    assert trace == ["validate_input", "honest_refusal"], f"Trace inesperado: {trace}"
    assert "retrieve" not in trace, "El nodo retrieve no debió ejecutarse."
    assert "generate_answer" not in trace, "El nodo generate_answer no debió ejecutarse."
    assert state.get("error") == "empty_question"
    assert len(state["answer"]) > 0


def test_eval_2_node_execution_order_retrieve_before_generation():
    """
    Eval 2: Cuando hay contexto, retrieve debe ejecutarse estrictamente ANTES que generate_answer.
    """
    checkpointer = MemorySaver()
    app = create_agent_graph(checkpointer=checkpointer)
    mock_context = [
        {
            "text": "Nexova Solutions ofrece servicios de consultoría tecnológica.",
            "source_document": "company-BRIEFING.md",
            "section": "Servicios",
            "score": 0.89,
        }
    ]
    with patch("services.agent.nodes.retrieve", return_value=mock_context):
        with patch("services.agent.nodes.generate_answer", return_value="Nexova ofrece consultoría."):
            thread_config = {"configurable": {"thread_id": "eval-order"}}
            state = app.invoke(
                {
                    "question": "¿Qué servicios ofrece Nexova?",
                    "context": [],
                    "answer": "",
                    "error": None,
                    "execution_trace": [],
                },
                config=thread_config,
            )
            trace = state["execution_trace"]
            assert "retrieve" in trace, "retrieve debe estar en el trace."
            assert "generate_answer" in trace, "generate_answer debe estar en el trace."
            assert trace.index("retrieve") < trace.index("generate_answer"), (
                "retrieve debe ejecutarse antes que generate_answer."
            )
            assert "honest_refusal" not in trace, "No debió ocurrir rechazo honesto."
            assert trace == ["validate_input", "retrieve", "generate_answer"]

def test_eval_3_honest_refusal_when_no_context():
    """
    Eval 3: Si retrieve devuelve contexto vacío (sin coincidencias sobre umbral 0.70),
    el grafo debe enrutar a honest_refusal y NO invocar generate_answer.
    """
    checkpointer = MemorySaver()
    app = create_agent_graph(checkpointer=checkpointer)
    with patch("services.agent.nodes.retrieve", return_value=[]):
        thread_config = {"configurable": {"thread_id": "eval-no-context"}}
        state = app.invoke(
            {
                "question": "¿Tienen paquetes turísticos a Júpiter?",
                "context": [],
                "answer": "",
                "error": None,
                "execution_trace": [],
            },
            config=thread_config,
        )
        trace = state["execution_trace"]
        assert trace == ["validate_input", "retrieve", "honest_refusal"]
        assert "generate_answer" not in trace, "generate_answer no debe llamarse si context está vacío."
        assert "no contiene información" in state["answer"].lower()

def test_eval_4_grounded_answer_briefing_policy():
    """
    Eval 4 (Anclaje al BRIEFING):
    Verifica que ante una consulta sobre políticas corporativas, la respuesta contenga
    el dato fáctico exacto de company-BRIEFING.md (garantía de reposición de 90 días naturales).
    """
    checkpointer = MemorySaver()
    app = create_agent_graph(checkpointer=checkpointer)
    mock_briefing_chunk = [
        {
            "text": (
                "La garantía de reposición en los procesos de headhunting de Nexova Solutions "
                "es de 90 días naturales, contados desde el primer día de incorporación efectiva."
            ),
            "source_document": "company-BRIEFING.md",
            "section": "Políticas y Garantías",
            "score": 0.94,
        }
    ]
    with patch("services.agent.nodes.retrieve", return_value=mock_briefing_chunk):
        thread_config = {"configurable": {"thread_id": "eval-grounding"}}
        state = app.invoke(
            {
                "question": "¿Cuál es la garantía de reposición en headhunting?",
                "context": [],
                "answer": "",
                "error": None,
                "execution_trace": [],
            },
            config=thread_config,
        )
        # Criterios verificables de anclaje:
        answer = state["answer"]
        assert "90 días" in answer or "90" in answer, "La respuesta debe mencionar el plazo de 90 días."
        assert state["execution_trace"] == ["validate_input", "retrieve", "generate_answer"]


def test_eval_5_checkpointing_state_inspection():
    """
    Eval 5: Verifica que el checkpointer guarda el snapshot del estado tras la corrida
    y permite inspeccionar el trace y los valores generados.
    """
    checkpointer = MemorySaver()
    app = create_agent_graph(checkpointer=checkpointer)
    thread_config = {"configurable": {"thread_id": "eval-checkpoint-thread"}}
    state = app.invoke(
        {
            "question": "   ",
            "context": [],
            "answer": "",
            "error": None,
            "execution_trace": [],
        },
        config=thread_config,
    )
    # Inspeccionar el estado guardado en el checkpointer
    saved_snapshot = app.get_state(thread_config)
    assert saved_snapshot is not None
    assert saved_snapshot.values["execution_trace"] == state["execution_trace"]
    assert saved_snapshot.values["answer"] == state["answer"]

def test_eval_6_agent_endpoint_unauthorized():
    """
    Eval 6: Verifica que el endpoint /agent/query rechaza con 401 Unauthorized
    cualquier petición sin token de autenticación (Auth Guard Standard).
    """
    client = TestClient(app)
    response = client.post("/agent/query", json={"question": "¿Cuál es la garantía?"})
    assert response.status_code == 401

def test_eval_7_agent_endpoint_authenticated():
    """
    Eval 7: Verifica que una petición autenticada al endpoint /agent/query
    retorna 200 OK con el execution_trace y la respuesta sintetizada.
    """
    client = TestClient(app)
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "admin-test-id",
        "email": "admin@nexova.com",
        "role": "admin",
    }
    mock_chunks = [
        {
            "text": "Garantía de reposición de 90 días naturales.",
            "source_document": "company-BRIEFING.md",
            "section": "Garantías",
            "score": 0.95,
        }
    ]
    try:
        with patch("services.agent.nodes.retrieve", return_value=mock_chunks):
            response = client.post("/agent/query", json={"question": "¿Cuál es la garantía?"})
            assert response.status_code == 200
            data = response.json()
            assert data["execution_trace"] == ["validate_input", "retrieve", "generate_answer"]
            assert data["sources_count"] == 1
            assert "thread_id" in data
            assert len(data["answer"]) > 0
    finally:
        app.dependency_overrides.clear()