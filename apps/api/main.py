from __future__ import annotations

from fastapi import Body, FastAPI, HTTPException

from core.events import InMemoryEventBus
from core.models import ActionRequest, CaseRecord, CreateCaseRequest, RepairOrderRequest
from core.orchestrator import GovernanceOrchestrator
from core.permissions import get_permission_matrix
from core.registry import CaseRegistry
from core.state_machine import transition_matrix


app = FastAPI(
    title="RegentOS API",
    version="0.1.0",
    description="A governance-first multi-agent MVP control plane.",
)

registry = CaseRegistry()
event_bus = InMemoryEventBus()
orchestrator = GovernanceOrchestrator(registry=registry, event_bus=event_bus)


def _handle(action):
    try:
        return action()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "regentos-api"}


@app.get("/api/cases", response_model=list[CaseRecord])
def list_cases() -> list[CaseRecord]:
    return orchestrator.list_cases()


@app.post("/api/cases", response_model=CaseRecord, status_code=201)
def create_case(payload: CreateCaseRequest) -> CaseRecord:
    return _handle(lambda: orchestrator.create_case(payload))


@app.get("/api/cases/{case_id}", response_model=CaseRecord)
def get_case(case_id: str) -> CaseRecord:
    return _handle(lambda: orchestrator.get_case(case_id))


@app.get("/api/cases/{case_id}/timeline")
def get_case_timeline(case_id: str) -> list[dict]:
    return _handle(lambda: orchestrator.get_timeline(case_id))


@app.get("/api/cases/{case_id}/dossier")
def get_case_dossier(case_id: str) -> dict:
    return _handle(lambda: orchestrator.get_dossier(case_id))


@app.post("/api/cases/{case_id}/accept", response_model=CaseRecord)
def accept_case(case_id: str, request: ActionRequest | None = Body(default=None)) -> CaseRecord:
    actor = request.actor if request else "personal_tongzhengsi"
    return _handle(lambda: orchestrator.accept_case(case_id, actor))


@app.post("/api/cases/{case_id}/submit-for-approval", response_model=CaseRecord)
def submit_for_approval(case_id: str, request: ActionRequest | None = Body(default=None)) -> CaseRecord:
    actor = request.actor if request else "cabinet"
    return _handle(lambda: orchestrator.submit_for_approval(case_id, actor))


@app.post("/api/cases/{case_id}/approve", response_model=CaseRecord)
def approve_case(case_id: str, request: ActionRequest | None = Body(default=None)) -> CaseRecord:
    actor = request.actor if request else "silijian"
    return _handle(lambda: orchestrator.approve_case(case_id, actor))


@app.post("/api/cases/{case_id}/reject", response_model=CaseRecord)
def reject_case(case_id: str, request: ActionRequest = Body(default_factory=ActionRequest)) -> CaseRecord:
    return _handle(lambda: orchestrator.reject_case(case_id, request))


@app.post("/api/cases/{case_id}/dispatch", response_model=CaseRecord)
def dispatch_case(case_id: str, request: ActionRequest | None = Body(default=None)) -> CaseRecord:
    actor = request.actor if request else "cabinet"
    return _handle(lambda: orchestrator.dispatch_case(case_id, actor))


@app.post("/api/cases/{case_id}/start-execution", response_model=CaseRecord)
def start_execution(case_id: str, request: ActionRequest | None = Body(default=None)) -> CaseRecord:
    actor = request.actor if request else "executor_pool"
    return _handle(lambda: orchestrator.start_execution(case_id, actor))


@app.post("/api/cases/{case_id}/report", response_model=CaseRecord)
def mark_reporting(case_id: str, request: ActionRequest | None = Body(default=None)) -> CaseRecord:
    actor = request.actor if request else "cabinet"
    return _handle(lambda: orchestrator.mark_reporting(case_id, actor))


@app.post("/api/cases/{case_id}/archive", response_model=CaseRecord)
def archive_case(case_id: str, request: ActionRequest | None = Body(default=None)) -> CaseRecord:
    actor = request.actor if request else "cabinet"
    return _handle(lambda: orchestrator.archive_case(case_id, actor))


@app.post("/api/cases/{case_id}/repair-pending", response_model=CaseRecord)
def repair_pending(case_id: str, request: ActionRequest = Body(default_factory=ActionRequest)) -> CaseRecord:
    return _handle(lambda: orchestrator.mark_repair_pending(case_id, request))


@app.post("/api/cases/{case_id}/repair-order", response_model=CaseRecord)
def repair_order(case_id: str, request: RepairOrderRequest) -> CaseRecord:
    return _handle(lambda: orchestrator.authorize_repair(case_id, request))


@app.post("/api/cases/{case_id}/rerun", response_model=CaseRecord)
def rerun_case(case_id: str, request: ActionRequest | None = Body(default=None)) -> CaseRecord:
    actor = request.actor if request else "executor_pool"
    return _handle(lambda: orchestrator.rerun_case(case_id, actor))


@app.post("/api/cases/{case_id}/pause", response_model=CaseRecord)
def pause_case(case_id: str, request: ActionRequest = Body(default_factory=ActionRequest)) -> CaseRecord:
    return _handle(lambda: orchestrator.pause_case(case_id, request))


@app.post("/api/cases/{case_id}/resume", response_model=CaseRecord)
def resume_case(case_id: str, request: ActionRequest = Body(default_factory=ActionRequest)) -> CaseRecord:
    return _handle(lambda: orchestrator.resume_case(case_id, request))


@app.post("/api/cases/{case_id}/freeze", response_model=CaseRecord)
def freeze_case(case_id: str, request: ActionRequest = Body(default_factory=ActionRequest)) -> CaseRecord:
    return _handle(lambda: orchestrator.freeze_case(case_id, request))


@app.post("/api/cases/{case_id}/cancel", response_model=CaseRecord)
def cancel_case(case_id: str, request: ActionRequest = Body(default_factory=ActionRequest)) -> CaseRecord:
    return _handle(lambda: orchestrator.cancel_case(case_id, request))


@app.get("/api/agents")
def list_agents() -> list[dict]:
    return [agent.model_dump(mode="json") for agent in orchestrator.list_agents()]


@app.get("/api/models/runtime-capabilities")
def runtime_capabilities() -> list[dict]:
    return [capability.model_dump(mode="json") for capability in orchestrator.runtime_capabilities()]


@app.get("/api/governance/permissions")
def permissions_matrix() -> dict:
    return get_permission_matrix()


@app.get("/api/governance/state-machine")
def state_machine_matrix() -> dict[str, list[str]]:
    return transition_matrix()

