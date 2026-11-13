"""
Define el esquema del estado mínimo y explícito que viaja entre los nodos de LangGraph.
"""
from typing import TypedDict, List, Dict, Any, Optional
class AgentState(TypedDict):
    """
    Estado del grafo del agente.
    
    Campos:
    - question: La pregunta formulada por el usuario.
    - intent: Intención clasificada autónomamente ("rag" | "incident_tool" | "unknown").
    - context: Lista de fragmentos (chunks) recuperados por el nodo retrieve (RAG).
    - tool_data: Datos devueltos por la herramienta externa de incidentes.
    - answer: La respuesta final generada, resultado de la tool o mensaje de fallback.
    - error: Detalle de error si la pregunta es inválida o vacía.
    - execution_trace: Registro secuencial de nodos recorridos para auditoría y evals.
    """
    question: str
    intent: Optional[str]
    context: List[Dict[str, Any]]
    tool_data: Optional[Dict[str, Any]]
    answer: str
    error: Optional[str]
    execution_trace: List[str]