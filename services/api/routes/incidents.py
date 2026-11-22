from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query as FastAPIQuery
from typing import List, Optional
from packages.shared.validation import (
    IncidentCreate, IncidentUpdateStatus, IncidentAssignUpdate, IncidentNoteCreate,
    IncidentResponse, IncidentInDB,
    IncidentStatus, IncidentOrigin, IncidentBranch, IncidentCategory
)
from services.api.database import get_tinydb as get_db
from services.api.routes.auth import get_current_user
from tinydb import Query
from services.api.models import IncidentSummaryResponse

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

@router.post("", response_model=IncidentResponse, status_code=201)
def create_incident(incident: IncidentCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    incidents_table = db.table('incidents')
    
    try:
        db_record = IncidentInDB(**incident.model_dump())
    except ValueError:
        raise HTTPException(status_code=400, detail="Datos de incidencia inválidos o incompletos.")
        
    # La inserción se asume segura o será capturada globalmente por FastAPI como 500
    incidents_table.insert(db_record.model_dump())
    return db_record


@router.get("", response_model=List[IncidentResponse])
def get_incidents(
    status: Optional[IncidentStatus] = None,
    origin: Optional[IncidentOrigin] = None,
    branch: Optional[IncidentBranch] = None,
    category: Optional[IncidentCategory] = None,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    incidents_table = db.table('incidents')
    records = incidents_table.all()
    
    if status:
        records = [r for r in records if r.get('status') == status]
    if origin:
        records = [r for r in records if r.get('origin') == origin]
    if branch:
        records = [r for r in records if r.get('branch') == branch]
    if category:
        records = [r for r in records if r.get('category') == category]
        
    return records


@router.get("/summary", response_model=IncidentSummaryResponse)
def get_summary(current_user: dict = Depends(get_current_user)):
    db = get_db()
    incidents_table = db.table('incidents')
    records = incidents_table.all()
    
    summary = {
        "status": {},
        "category": {},
        "origin": {},
        "branch": {}
    }
    
    for r in records:
        st = r.get('status')
        ca = r.get('category')
        ori = r.get('origin')
        br = r.get('branch')
        
        if st: summary["status"][st] = summary["status"].get(st, 0) + 1
        if ca: summary["category"][ca] = summary["category"].get(ca, 0) + 1
        if ori: summary["origin"][ori] = summary["origin"].get(ori, 0) + 1
        if br: summary["branch"][br] = summary["branch"].get(br, 0) + 1
        
    return summary


@router.get("/{id}", response_model=IncidentResponse)
def get_incident(id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    incidents_table = db.table('incidents')
    IncidentQ = Query()
    result = incidents_table.search(IncidentQ.id == id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
        
    return result[0]

    
@router.patch("/{id}/status", response_model=IncidentResponse)
def update_status(id: str, update: IncidentUpdateStatus, current_user: dict = Depends(get_current_user)):
    db = get_db()
    incidents_table = db.table('incidents')
    IncidentQ = Query()
    result = incidents_table.search(IncidentQ.id == id)

    if not result:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    current_record = result[0]
    role_raw = current_user.get("role", "user")
    role = str(getattr(role_raw, "value", role_raw)).lower()
    if role != "admin":
        caller_raw = current_user.get("tenant_id") or current_user.get("branch") or ""
        target_raw = current_record.get("tenant_id") or current_record.get("branch") or ""
        caller_tenant = str(getattr(caller_raw, "value", caller_raw)).strip().lower()
        target_tenant = str(getattr(target_raw, "value", target_raw)).strip().lower()
        if not caller_tenant or not target_tenant or caller_tenant != target_tenant:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para modificar incidencias de otro tenant.",
            )

    current_status = current_record.get('status')
    new_status = update.status
    
    valid_transitions = {
        IncidentStatus.open: [IncidentStatus.in_progress, IncidentStatus.discarded],
        IncidentStatus.in_progress: [IncidentStatus.resolved, IncidentStatus.discarded],
        IncidentStatus.resolved: [],
        IncidentStatus.discarded: []
    }
    
    if current_status == new_status:
        return current_record
        
    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Transición de estado no válida. No se puede pasar de {current_status} a {new_status}."
        )
        
    incidents_table.update(
        {"status": new_status, "updated_at": datetime.utcnow().isoformat()},
        IncidentQ.id == id,
    )
    
    updated_record = incidents_table.search(IncidentQ.id == id)[0]
    return updated_record


@router.patch("/{id}/assign", response_model=IncidentResponse)
def assign_incident(
    id: str,
    payload: IncidentAssignUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Asigna o desasigna un responsable a la incidencia."""
    db = get_db()
    incidents_table = db.table('incidents')
    IncidentQ = Query()
    result = incidents_table.search(IncidentQ.id == id)
    if not result:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    assigned = payload.assigned_to.strip() if payload.assigned_to else None
    incidents_table.update(
        {"assigned_to": assigned or None, "updated_at": datetime.utcnow().isoformat()},
        IncidentQ.id == id,
    )
    return incidents_table.search(IncidentQ.id == id)[0]


@router.post("/{id}/notes", response_model=IncidentResponse)
def add_incident_note(
    id: str,
    payload: IncidentNoteCreate,
    current_user: dict = Depends(get_current_user),
):
    """Registra una nota de seguimiento o resolución en la incidencia."""
    db = get_db()
    incidents_table = db.table('incidents')
    IncidentQ = Query()
    result = incidents_table.search(IncidentQ.id == id)
    if not result:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")

    current_record = result[0]
    notes = list(current_record.get("resolution_notes") or [])
    author = str(current_user.get("email") or current_user.get("username") or "Agente")
    notes.append(
        {
            "id": str(uuid.uuid4()),
            "author": author,
            "content": payload.content.strip(),
            "created_at": datetime.utcnow().isoformat(),
        }
    )
    incidents_table.update(
        {"resolution_notes": notes, "updated_at": datetime.utcnow().isoformat()},
        IncidentQ.id == id,
    )
    return incidents_table.search(IncidentQ.id == id)[0]
