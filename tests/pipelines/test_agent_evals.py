"""
tests/pipelines/test_agent_evals.py
Suite de evaluación (evals) para el agente de soporte con LangGraph.
Verifica:
1. Enrutamiento del trace ante preguntas vacías.
2. Orden estricto de ejecución: retrieve antes que generate_answer.
3. Rechazo honesto ante ausencia de contexto sobre el umbral.
4. Anclaje de la respuesta en la base documental oficial (company-BRIEFING.md).
5. Persistencia e inspección mediante checkpointing.
6. Seguridad Auth Guard en endpoint /agent/query (401 Unauthorized).
7. Ejecución autenticada en endpoint /agent/query (200 OK con trace).
8. Enrutamiento autónomo hacia herramienta externa de incidencias (Tool route).
9. Enrutamiento autónomo hacia RAG para consultas de políticas/normativas.
10. Ruta de fallback honesto ante ticket inexistente.
11. Resiliencia ante timeout o fallos de red de la herramienta externa.
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
    sin ejecutar classify_intent, retrieve ni generate_answer.
    """
    checkpointer = MemorySaver()
    agent = create_agent_graph(checkpointer=checkpointer)
    thread_config = {"configurable": {"thread_id": "eval-empty-q"}}
    state = agent.invoke(
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
    assert "classify_intent" not in trace
    assert "retrieve" not in trace
    assert "generate_answer" not in trace
    assert state.get("error") == "empty_question"
    assert len(state["answer"]) > 0


def test_eval_2_node_execution_order_retrieve_before_generation():
    """
    Eval 2: Cuando hay contexto documental, retrieve debe ejecutarse estrictamente ANTES que generate_answer.
    """
    checkpointer = MemorySaver()
    agent = create_agent_graph(checkpointer=checkpointer)
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
            state = agent.invoke(
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
            assert trace == ["validate_input", "classify_intent", "retrieve", "generate_answer"]


def test_eval_3_honest_refusal_when_no_context():
    """
    Eval 3: Si retrieve devuelve contexto vacío (sin coincidencias sobre umbral 0.70),
    el grafo debe enrutar a honest_refusal y NO invocar generate_answer.
    """
    checkpointer = MemorySaver()
    agent = create_agent_graph(checkpointer=checkpointer)
    with patch("services.agent.nodes.retrieve", return_value=[]):
        thread_config = {"configurable": {"thread_id": "eval-no-context"}}
        state = agent.invoke(
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
        assert trace == ["validate_input", "classify_intent", "retrieve", "honest_refusal"]
        assert "generate_answer" not in trace, "generate_answer no debe llamarse si context está vacío."
        assert "no contiene información" in state["answer"].lower()


def test_eval_4_grounded_answer_briefing_policy():
    """
    Eval 4 (Anclaje al BRIEFING):
    Verifica que ante una consulta sobre políticas corporativas, la respuesta contenga
    el dato fáctico exacto de company-BRIEFING.md (garantía de reposición de 90 días naturales).
    """
    checkpointer = MemorySaver()
    agent = create_agent_graph(checkpointer=checkpointer)
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
        state = agent.invoke(
            {
                "question": "¿Cuál es la garantía de reposición en headhunting?",
                "context": [],
                "answer": "",
                "error": None,
                "execution_trace": [],
            },
            config=thread_config,
        )
        answer = state["answer"]
        assert "90 días" in answer or "90" in answer, "La respuesta debe mencionar el plazo de 90 días."
        assert state["execution_trace"] == ["validate_input", "classify_intent", "retrieve", "generate_answer"]


def test_eval_5_checkpointing_state_inspection():
    """
    Eval 5: Verifica que el checkpointer guarda el snapshot del estado tras la corrida
    y permite inspeccionar el trace y los valores generados.
    """
    checkpointer = MemorySaver()
    agent = create_agent_graph(checkpointer=checkpointer)
    thread_config = {"configurable": {"thread_id": "eval-checkpoint-thread"}}
    state = agent.invoke(
        {
            "question": "   ",
            "context": [],
            "answer": "",
            "error": None,
            "execution_trace": [],
        },
        config=thread_config,
    )
    saved_snapshot = agent.get_state(thread_config)
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
            assert data["execution_trace"] == ["validate_input", "classify_intent", "retrieve", "generate_answer"]
            assert data["sources_count"] == 1
            assert "thread_id" in data
            assert len(data["answer"]) > 0
    finally:
        app.dependency_overrides.clear()


# =========================================================================
# EVALS PARTE 2: HERRAMIENTAS EXTERNAS Y ENRUTAMIENTO AUTÓNOMO
# =========================================================================

def test_eval_8_autonomous_routing_to_incident_tool():
    """
    Eval 8: Una consulta que menciona un número de ticket debe ser enrutada
    autónomamente a la herramienta externa (incident_tool -> format_tool_answer),
    sin pasar por el recuperador documental (retrieve).
    """
    checkpointer = MemorySaver()
    agent = create_agent_graph(checkpointer=checkpointer)
    thread_config = {"configurable": {"thread_id": "eval-tool-ticket-1"}}
    
    state = agent.invoke(
        {
            "question": "¿Podrías darme el estado actual del ticket #1?",
            "context": [],
            "answer": "",
            "error": None,
            "execution_trace": [],
        },
        config=thread_config,
    )
    
    trace = state["execution_trace"]
    assert "classify_intent" in trace, "classify_intent debe estar en el trace."
    assert "incident_tool" in trace, "incident_tool debe ser ejecutado."
    assert "format_tool_answer" in trace, "format_tool_answer debe formatear el resultado."
    assert "retrieve" not in trace, "No debe invocar retrieve en consultas de incidencias."
    assert "generate_answer" not in trace, "No debe invocar generate_answer en consultas de incidencias."
    assert trace == ["validate_input", "classify_intent", "incident_tool", "format_tool_answer"]
    
    # Verificación de datos del ticket en la respuesta
    assert state.get("tool_data") is not None
    assert "ticket" in state["answer"].lower() or "incidencia" in state["answer"].lower()


def test_eval_9_autonomous_routing_to_rag():
    """
    Eval 9: Una consulta sobre normativas/políticas debe enrutarse autónomamente a RAG,
    sin consultar la herramienta de incidencias.
    """
    checkpointer = MemorySaver()
    agent = create_agent_graph(checkpointer=checkpointer)
    mock_policy = [
        {
            "text": "Política de confidencialidad de Nexova Solutions.",
            "source_document": "company-BRIEFING.md",
            "section": "Políticas",
            "score": 0.92,
        }
    ]
    with patch("services.agent.nodes.retrieve", return_value=mock_policy):
        with patch("services.agent.nodes.generate_answer", return_value="Nexova exige estricta confidencialidad."):
            thread_config = {"configurable": {"thread_id": "eval-rag-route"}}
            state = agent.invoke(
                {
                    "question": "¿Cuál es la política de confidencialidad de la empresa?",
                    "context": [],
                    "answer": "",
                    "error": None,
                    "execution_trace": [],
                },
                config=thread_config,
            )
            trace = state["execution_trace"]
            assert trace == ["validate_input", "classify_intent", "retrieve", "generate_answer"]
            assert "incident_tool" not in trace, "incident_tool no debe llamarse en consultas documentales."
            assert "tool_fallback" not in trace


def test_eval_10_incident_tool_fallback_on_missing_ticket():
    """
    Eval 10: Cuando se consulta un ticket que no existe en el gestor de incidencias,
    el grafo debe ejecutar tool_fallback y dar una respuesta honesta sin alucinar.
    """
    checkpointer = MemorySaver()
    agent = create_agent_graph(checkpointer=checkpointer)
    thread_config = {"configurable": {"thread_id": "eval-tool-missing-ticket"}}
    
    state = agent.invoke(
        {
            "question": "¿Cuál es el estatus del ticket #99999999?",
            "context": [],
            "answer": "",
            "error": None,
            "execution_trace": [],
        },
        config=thread_config,
    )
    
    trace = state["execution_trace"]
    assert trace == ["validate_input", "classify_intent", "incident_tool", "tool_fallback"]
    assert "format_tool_answer" not in trace, "No debe formatear respuesta exitosa si no existe."
    assert "no pude confirmar el estado de ese ticket" in state["answer"].lower()
    assert state.get("tool_data") is None


def test_eval_11_incident_tool_timeout_resilience():
    """
    Eval 11: Resiliencia ante fallos de red o timeouts en la herramienta externa.
    Si la herramienta lanza TimeoutError o excepción, debe activar tool_fallback honestamente.
    """
    checkpointer = MemorySaver()
    agent = create_agent_graph(checkpointer=checkpointer)
    thread_config = {"configurable": {"thread_id": "eval-tool-timeout"}}
    
    with patch("services.agent.nodes.get_incident_ticket", side_effect=TimeoutError("Connection timed out after 5.0s")):
        state = agent.invoke(
            {
                "question": "Dime el estado del ticket #1",
                "context": [],
                "answer": "",
                "error": None,
                "execution_trace": [],
            },
            config=thread_config,
        )
        trace = state["execution_trace"]
        assert trace == ["validate_input", "classify_intent", "incident_tool", "tool_fallback"]
        assert "no pude confirmar el estado de ese ticket" in state["answer"].lower()