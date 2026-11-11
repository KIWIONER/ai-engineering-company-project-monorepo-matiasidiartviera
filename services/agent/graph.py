"""
Construcción, enrutamiento condicional y compilación del grafo del agente de soporte con LangGraph.
Incluye checkpointing en memoria para auditoría e inspección de transiciones.
"""

from typing import Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from services.agent.state import AgentState
from services.agent.nodes import (
    validate_input_node,
    retrieve_node,
    honest_refusal_node,
    generate_answer_node,
)

def route_after_validation(state: AgentState) -> str:
    """
    Arista condicional 1:
    Si hay error de validación (pregunta vacía), enruta al rechazo honesto.
    Si la pregunta es válida, avanza a la recuperación de contexto.
    """
    if state.get("error"):
        return "honest_refusal"
    return "retrieve"

def route_after_retrieval(state: AgentState) -> str:
    """
    Arista condicional 2:
    Si se encontraron documentos relevantes, procede a generar respuesta.
    Si no hay contexto suficiente sobre el umbral, enruta al rechazo honesto.
    """
    context = state.get("context", [])
    if context and len(context) > 0:
        return "generate_answer"
    return "honest_refusal"

def create_agent_graph(checkpointer: Optional[MemorySaver] = None):
    """
    Crea, conecta y compila el StateGraph del agente.
    La compilación falla en build-time si la topología tiene inconsistencias.
    """
    workflow = StateGraph(AgentState)

    # 1. Registrar nodos con responsabilidad única
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("honest_refusal", honest_refusal_node)
    workflow.add_node("generate_answer", generate_answer_node)

    #2 Conectar punto de entrada
    workflow.add_edge(START, "validate_input")

    #3 Asitas condicionales (no es una línea recta)
    workflow.add_conditional_edges(
        "validate_input", route_after_validation,
        {
        "retrieve": "retrieve",
        "honest_refusal": "honest_refusal",
        },
    )
    workflow.add_conditional_edges(
        "retrieve", route_after_retrieval,
        {
        "generate_answer": "generate_answer",
        "honest_refusal": "honest_refusal",
        },
    )
    
    #4 Conectar salidas hacia el final
    workflow.add_edge("honest_refusal", END)
    workflow.add_edge("generate_answer", END)

    #5 Compilar con checkpointer para auditoria de estados.
    active_checkpointer = checkpointer if checkpointer is not None else MemorySaver()
    compiled_app =  workflow.compile(checkpointer=active_checkpointer)

    return compiled_app

# Instancia compilada por defecto lista para ser consumida
default_checkpointer = MemorySaver()
agent_app = create_agent_graph(checkpointer=default_checkpointer)


def run_agent(question: str, thread_id: str = "default-thread") -> AgentState:
    """
    Función de ejecución conveniente para correr una pregunta contra el grafo.
    Devuelve el estado final con su respuesta y execution_trace completo.
    """
    initial_state: AgentState = {
        "question": question,
        "context": [],
        "answer": "",
        "error": None,
        "execution_trace": [],
    }
    config = {"configurable": {"thread_id": thread_id}}
    final_state = agent_app.invoke(initial_state, config=config)
    return final_state
