"""
Define el esquema del estado mínimo y explícito que viaja entre los nodos de LangGraph.
"""
from typing import TypedDict, List, Dict, Any, Optional
class AgentState(TypedDict):
    """
    Estado del grafo del agente.
    
    Campos mínimos:
    - question: La pregunta formulada por el usuario.
    - context: Lista de fragmentos (chunks) recuperados por el nodo retrieve.
    - answer: La respuesta final generada o el mensaje de rechazo honesto.
    - error: Detalle de error si la pregunta es inválida o vacía.
    - execution_trace: Registro secuencial de nodos recorridos para auditoría y evals.
    """
    question: str
    context: List[Dict[str, Any]]
    answer: str
    error: Optional[str]
    execution_trace: List[str]