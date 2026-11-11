"""
services/agent/nodes.py
Nodos con responsabilidad única para el grafo de LangGraph.
Reutiliza data.pipelines.rag sin duplicar lógica ni re-envolver query() monolítico.
"""

import logging
from typing import Dict, Any
from services.agent.state import AgentState
from data.pipelines.rag import retrieve, generate_answer
logger = logging.getLogger(__name__)

def validate_input_node(state: AgentState)-> Dict[str, Any]:
    """
    Nodo 1: Valida que la pregunta del usuario no esté vacía.
    Actualiza el execution_trace para auditoría.
    """
    question= state.get("question","").strip()
    trace= list(state.get("execution_trace", [])) + ["validate_input"]

    if not question:
        return{
            "question":"",
            "error": "empty_question",
            "answer": "la consulta no puede estar vacía. Por favor, formula una pregunta válida",
            "execution_trace": trace,
        }
    return{
        "question": question,
        "error": None,
        "execution_trace": trace,
    }

def retrieve_node(state: AgentState)-> Dict[str, Any]:
    """
    Nodo 2: Ejecuta la recuperación sobre la base de conocimiento vectorial.
    Reutiliza data.pipelines.rag.retrieve() con umbral de relevancia (min_score=0.70).
    """
    question = state["question"]
    trace= list(state.get("execution_trace", [])) + ["retrieve"]

    try:
        context= retrieve(question, min_score=0.70)
    except Exception as exc:
        logger.error(f"Error al ejecutar retrieve en base vectorial: {exc}")
        context=[]
    return {
        "context": context,
        "execution_trace": trace,
    }

def honest_refusal_node(state: AgentState)-> Dict[str, Any]:
    """
    Nodo 3: Respuesta honesta si no hay contexto suficiente o si hubo error de validación.
    Previene alucinaciones al no forzar la llamada al LLM sobre vacío.
    """
    trace= list(state.get ("execution_trace", [])) + ["honest_refusal"]

    if state.get("error") == "empty_question":
        answer= state.get("answer", "La consulta no puede estar vacía")
    else:
        answer= "Lo siento, la documentación corporativa actual de Nexova Solution no contiene información sobe esa consulta"
    return{
        "answer": answer,
        "execution_trace": trace,
    }    

def generate_answer_node(state: AgentState)-> Dict[str, Any]:
    """
    Nodo 4: Genera la respuesta final utilizando exclusivamente los fragmentos recuperados.
    Reutiliza data.pipelines.rag.generate_answer().
    """
    question= state["question"]
    context= state.get("context", [])
    trace= list(state.get("execution_trace", [])) + ["generate_answer"]

    answer= generate_answer(question, context)

    return{
        "answer": answer,
        "execution_trace": trace,
    }