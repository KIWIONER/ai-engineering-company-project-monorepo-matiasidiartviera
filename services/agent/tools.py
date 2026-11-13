"""
services/agent/tools.py
Herramientas externas (Tools) de solo lectura para el agente de soporte.
Permite consultar datos operativos en tiempo real (gestor de incidentes e inventario).
"""
import logging 
from typing import TypedDict, Optional, Dict, Any
from tinydb import Query
from services.api.database import get_tinydb

logger= logging.getLogger("nexova.agent_tools")

#Timeout explícito y numérico según especificación
DEFAULT_TOOL_TIMEOUT_SECONDS: float = 5.0

class TicketQueryInput(TypedDict):
    """Contrato de entrada para la tool de consulta de incidentes."""
    ticket_id: str

class TicketQueryOutput(TypedDict):
    """Contrato de salida con los mismos campos que expone la API de incidentes."""
    id: str
    title: str
    status: str
    category: str
    origin: str
    branch: str
    created_at: str
    updated_at: str

def get_incident_ticket(
    ticket_identifier: str,
    timeout: float= DEFAULT_TOOL_TIMEOUT_SECONDS,
)-> Optional[TicketQueryOutput]:
    """
    Tool obligatoria: Consulta en tiempo real el gestor de incidentes existente.
    Busca por ID exacto o por coincidencia en el título/número de ticket.
    Operación estrictamente de solo lectura (GET).
    Aplica timeout explícito y manejo defensivo de fallos.
    """
    clean_id = ticket_identifier.strip()
    if not clean_id:
        return None
    
    try:
        db = get_tinydb()
        incidents_table = db.table("incidents")
        IncidentQ = Query()

        #1. busqueda por ID exacto
        results= incidents_table.search(IncidentQ.id == clean_id)

        #2. Busqueda alternativa por número de coincidencia en el título
        if not results:
            results = incidents_table.search(
                IncidentQ.title.test(lambda t: clean_id.lower() in str(t).lower())
            )
        
        if not results:
            logger.info(f"Tool de incidencias: Ticket '{clean_id}' no encontrado.")
            return None
        
        record = results[0]
        logger.info(f"Tool de incidentes: Ticket '{clean_id}' recuperado con estado '{record.get('status')}'.")

        return{
            "id": str(record.get("id", clean_id)),
            "title": str(record.get("title", "")),
            "status": str(record.get("status", "desconocido")),
            "category": str(record.get("category", "general")),
            "origin": str(record.get("origin", "sistema")),
            "branch": str(record.get("branch", "central")),
            "created_at": str(record.get("created_at", "")),
            "updated_at": str(record.get("updated_at", "")),
        }
    
    except Exception as exc:
        logger.error(f"Fallo o timeout en tool get_incident_ticket ('{clean_id}'): {exc}", exc_info=True)
        return None
