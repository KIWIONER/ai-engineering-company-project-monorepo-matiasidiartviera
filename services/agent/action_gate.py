"""
services/agent/action_gate.py
Puerta determinista de acciones (fail-secure), minimización de contexto RGPD
y registro forense de decisiones agénticas para Nexova Solutions.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("nexova.agent_audit")

Verdict = Literal["allowed", "confirm", "denied"]

SAFE_ACTIONS = frozenset({
    "incidents_get_status",
    "inventory_query_stock",
    "search_kb",
    "draft_response",
    "read_file",
})

# Acciones irreversibles del Briefing Nexova (§5) + comunicaciones externas
CONFIRM_ACTIONS = frozenset({
    "discard_candidate",          # Descartar candidato de un proceso de selección
    "send_commercial_proposal",   # Enviar propuesta comercial o contrato
    "resolve_sensitive_ticket",   # Marcar ticket con queja/dato sensible como resuelto
    "bulk_update_ats",            # Modificar estado de candidatos en ATS de forma masiva
    "send_email",
})

BULK_THRESHOLD = 10

_SECRET_PATTERN = re.compile(r"(sk-[A-Za-z0-9_\-]{8,}|Bearer\s+[A-Za-z0-9\-._~+/=]+)", re.IGNORECASE)
_SENSITIVE_KEYS = frozenset({"password", "secret", "token", "api_key", "salary", "pretension_salarial"})


class AgentAuditRecord(BaseModel):
    """Registro forense estructurado de cada decisión/acción de un agente."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: str
    tenant_id: Optional[str] = None
    model: str
    action_type: str
    verdict: Verdict
    reason: str
    sanitized_args: Dict[str, Any] = Field(default_factory=dict)


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return _SECRET_PATTERN.sub("[REDACTED]", value)
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if str(k).lower() in _SENSITIVE_KEYS else _sanitize_value(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value


class AgentAuditLogger:
    """Almacén observable y logger forense para decisiones de agentes."""

    def __init__(self) -> None:
        self._records: List[AgentAuditRecord] = []

    def log_decision(
        self,
        *,
        user_id: str,
        model: str,
        action_type: str,
        verdict: Verdict,
        reason: str,
        tenant_id: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None,
    ) -> AgentAuditRecord:
        sanitized = _sanitize_value(args or {})
        record = AgentAuditRecord(
            user_id=user_id,
            tenant_id=tenant_id,
            model=model,
            action_type=action_type,
            verdict=verdict,
            reason=reason,
            sanitized_args=sanitized if isinstance(sanitized, dict) else {},
        )
        self._records.append(record)
        logger.info(
            "[AGENT-AUDIT] ts=%s user=%s tenant=%s model=%s action=%s verdict=%s reason=%s",
            record.timestamp,
            record.user_id,
            record.tenant_id or "none",
            record.model,
            record.action_type,
            record.verdict,
            record.reason,
        )
        return record

    def get_records(self) -> List[Dict[str, Any]]:
        return [r.model_dump() for r in self._records]

    def reset(self) -> None:
        self._records.clear()


agent_audit_logger = AgentAuditLogger()


def review_action(
    action: Any,
    *,
    caller_tenant: Optional[str] = None,
) -> Verdict:
    """
    Puerta determinista fail-secure entre el agente y las herramientas:
    - 'denied': acción malformada, sin 'type', desconocida o con argumentos inseguros.
    - 'confirm': acción irreversible (Briefing §5) o reversible que supera BULK_THRESHOLD.
    - 'allowed': acción permitida, reversible y dentro de los límites seguros.
    """
    if not isinstance(action, dict):
        return "denied"

    action_type = action.get("type")
    if not isinstance(action_type, str) or not action_type.strip():
        return "denied"

    # Validación de aislamiento cross-tenant si ambos están presentes
    target_tenant = action.get("tenant_id")
    if caller_tenant and target_tenant:
        if str(caller_tenant).strip().lower() != str(target_tenant).strip().lower():
            return "denied"

    # Validación de traversal en rutas de archivo si aplica
    file_path = action.get("path")
    if isinstance(file_path, str) and (".." in file_path or file_path.startswith("/")):
        return "denied"

    if action_type in CONFIRM_ACTIONS:
        return "confirm"

    if action_type in SAFE_ACTIONS:
        records = action.get("records", 1)
        if not isinstance(records, int) or records < 0:
            return "denied"
        if records > BULK_THRESHOLD:
            return "confirm"
        return "allowed"

    return "denied"


def build_hitl_confirmation_message(action: Dict[str, Any]) -> str:
    """Genera un aviso HITL concreto con acción, recurso afectado e impacto."""
    action_type = str(action.get("type", "unknown"))
    target = str(action.get("target") or action.get("candidate_id") or action.get("ticket_id") or "recurso")
    records = action.get("records", 1)
    return (
        f"Confirmación humana requerida para acción irreversible '{action_type}' "
        f"sobre '{target}' (registros afectados: {records}). "
        f"Responde explícitamente para aprobar o rechazar."
    )


def minimize_user_context(
    record: Dict[str, Any],
    allowed_fields: Iterable[str],
) -> Dict[str, Any]:
    """
    Principio de minimización RGPD: extrae únicamente los campos permitidos
    antes de enviar contexto a un modelo de lenguaje.
    """
    allowed = set(allowed_fields)
    return {k: v for k, v in (record or {}).items() if k in allowed}