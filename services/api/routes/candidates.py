from fastapi import APIRouter, Depends, HTTPException, Query as FastAPIQuery
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from services.agent.action_gate import build_hitl_confirmation_message, review_action
from services.api.models import (
    CandidateCreate, CandidateResponse, CandidateUpdate, CandidatePatch,
    CandidateNoteCreate, CandidateNoteResponse
)
from services.api.database import (
    get_all_candidates_from_db, get_candidate_from_db, create_candidate_in_db,
    update_candidate_in_db, create_candidate_note_in_db, get_candidate_notes_from_db,
    delete_candidate_note_from_db
)
from services.api.routes.auth import get_current_user

router = APIRouter(prefix="/api/candidates", tags=["candidates"])

@router.get("", response_model=List[CandidateResponse])

@router.get("/", response_model=List[CandidateResponse], include_in_schema=False)
def get_candidates(
    status: Optional[str] = FastAPIQuery(None),
    stage: Optional[str] = FastAPIQuery(None),
    current_user: dict = Depends(get_current_user)
):
    return get_all_candidates_from_db(status=status, stage=stage)

@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: int, current_user: dict = Depends(get_current_user)):
    candidate = get_candidate_from_db(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.post("", response_model=CandidateResponse)
@router.post("/", response_model=CandidateResponse, include_in_schema=False)
def create_candidate(candidate: CandidateCreate, current_user: dict = Depends(get_current_user)):
    return create_candidate_in_db(candidate.dict())

class BulkCandidateUpdate(BaseModel):
    candidate_ids: List[int] = Field(..., min_length=1)
    status: Optional[str] = None
    stage: Optional[str] = None
    approved: bool = False


def _enforce_candidate_gate(
    action_type: str,
    target: str,
    records: int,
    approved: bool,
    current_user: dict,
):
    caller_tenant = current_user.get("tenant_id") or current_user.get("branch")
    gate_action = {"type": action_type, "target": target, "records": records}
    verdict = review_action(gate_action, caller_tenant=caller_tenant)
    if verdict == "denied":
        raise HTTPException(status_code=403, detail="Acción denegada por la compuerta de seguridad.")
    if verdict == "confirm" and not approved:
        return JSONResponse(
            status_code=202,
            content={
                "status": "hitl_confirmation_required",
                "requires_confirmation": True,
                "action": action_type,
                "target": target,
                "records": records,
                "message": build_hitl_confirmation_message(gate_action),
            },
        )
    return None


@router.patch("/bulk")
def bulk_update_candidates(
    payload: BulkCandidateUpdate,
    current_user: dict = Depends(get_current_user),
):
    gate_response = _enforce_candidate_gate(
        action_type="bulk_update_ats",
        target="candidates",
        records=len(payload.candidate_ids),
        approved=payload.approved,
        current_user=current_user,
    )
    if gate_response is not None:
        return gate_response

    updates = {k: v for k, v in {"status": payload.status, "stage": payload.stage}.items() if v is not None}
    updated = [update_candidate_in_db(cid, updates) for cid in payload.candidate_ids]
    return {"status": "success", "updated_count": len(updated), "candidates": updated}


@router.put("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(
    candidate_id: int,
    candidate: CandidateUpdate,
    approved: bool = FastAPIQuery(False),
    current_user: dict = Depends(get_current_user),
):
    existing = get_candidate_from_db(candidate_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Candidate not found")
    data = candidate.dict(exclude_unset=True)
    if str(data.get("status", "")).upper() == "REJECTED":
        gate_response = _enforce_candidate_gate(
            action_type="discard_candidate",
            target=str(candidate_id),
            records=1,
            approved=approved,
            current_user=current_user,
        )
        if gate_response is not None:
            return gate_response
    return update_candidate_in_db(candidate_id, data)


@router.patch("/{candidate_id}", response_model=CandidateResponse)
def patch_candidate(
    candidate_id: int,
    candidate: CandidatePatch,
    approved: bool = FastAPIQuery(False),
    current_user: dict = Depends(get_current_user),
):
    existing = get_candidate_from_db(candidate_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Candidate not found")
    data = candidate.dict(exclude_unset=True)
    if str(data.get("status", "")).upper() == "REJECTED":
        gate_response = _enforce_candidate_gate(
            action_type="discard_candidate",
            target=str(candidate_id),
            records=1,
            approved=approved,
            current_user=current_user,
        )
        if gate_response is not None:
            return gate_response
    return update_candidate_in_db(candidate_id, data)

@router.get("/{candidate_id}/notes", response_model=List[CandidateNoteResponse])
def get_candidate_notes(candidate_id: int, current_user: dict = Depends(get_current_user)):
    return get_candidate_notes_from_db(candidate_id)

@router.post("/{candidate_id}/notes", response_model=CandidateNoteResponse)
def add_candidate_note(candidate_id: int, note: CandidateNoteCreate, current_user: dict = Depends(get_current_user)):
    return create_candidate_note_in_db(candidate_id, note.dict())

@router.delete("/{candidate_id}/notes/{note_id}", status_code=204)
def delete_candidate_note(candidate_id: int, note_id: int, current_user: dict = Depends(get_current_user)):
    success = delete_candidate_note_from_db(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
