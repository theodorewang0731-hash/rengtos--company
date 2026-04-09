from __future__ import annotations

from uuid import uuid4

from core.events import GovernanceEvent, InMemoryEventBus
from core.models import (
    ActionRequest,
    AgentProfile,
    CaseRecord,
    CaseStatus,
    CreateCaseRequest,
    GovernanceLayer,
    RepairOrderRequest,
    RuntimeCapability,
    TimelineEvent,
)
from core.registry import CaseRegistry
from core.replay import export_case_dossier, export_timeline
from core.state_machine import assert_transition, is_terminal


AGENT_CATALOG = [
    AgentProfile(
        agent_id="personal_tongzhengsi",
        name="个人通政司",
        layer=GovernanceLayer.PERSONAL,
        office="通政司",
        duty="接收个人任务并完成案件化登记",
        deployment_hint="local",
    ),
    AgentProfile(
        agent_id="cabinet",
        name="内阁",
        layer=GovernanceLayer.COMPANY,
        office="内阁",
        duty="形成票拟方案并组织最小执行流转",
        deployment_hint="private-cloud",
    ),
    AgentProfile(
        agent_id="silijian",
        name="司礼监",
        layer=GovernanceLayer.COMPANY,
        office="司礼监",
        duty="审批、封驳与修复受令审定",
        deployment_hint="private-cloud",
    ),
    AgentProfile(
        agent_id="censorship",
        name="台谏院",
        layer=GovernanceLayer.COMPANY,
        office="台谏院",
        duty="常规监督、稽察与流程偏航记录",
        deployment_hint="private-cloud",
    ),
    AgentProfile(
        agent_id="jinyiwei",
        name="锦衣卫",
        layer=GovernanceLayer.COMPANY,
        office="锦衣卫",
        duty="特别监察、重大异常分级与上报",
        deployment_hint="hybrid",
    ),
]

RUNTIME_CAPABILITIES = [
    RuntimeCapability(
        agent_id="personal_tongzhengsi",
        preferred_backend="local",
        supported_backends=["local", "remote_api"],
        notes="最贴近终端上下文，优先本地部署。",
    ),
    RuntimeCapability(
        agent_id="cabinet",
        preferred_backend="remote_api",
        supported_backends=["remote_api", "private_cloud"],
        notes="擅长票拟、总结、协调与草案生成。",
    ),
    RuntimeCapability(
        agent_id="silijian",
        preferred_backend="private_cloud",
        supported_backends=["private_cloud", "remote_api"],
        notes="审批链宜部署在内网治理环境中。",
    ),
    RuntimeCapability(
        agent_id="censorship",
        preferred_backend="private_cloud",
        supported_backends=["private_cloud", "local"],
        notes="常规监督需要稳定接入事件流与审计档案。",
    ),
    RuntimeCapability(
        agent_id="jinyiwei",
        preferred_backend="hybrid",
        supported_backends=["local", "private_cloud", "remote_api"],
        notes="个人层贴近本地，部门和公司层集中做分级、归档与上报。",
    ),
]


class GovernanceOrchestrator:
    def __init__(self, registry: CaseRegistry, event_bus: InMemoryEventBus) -> None:
        self.registry = registry
        self.event_bus = event_bus

    def create_case(self, payload: CreateCaseRequest) -> CaseRecord:
        case = self.registry.create(payload)
        case.metadata.setdefault("repair_chain", [])
        self._append_event(
            case,
            event_type="case_created",
            actor=payload.submitted_by,
            from_status=None,
            to_status=case.status,
            message="案件已建立并完成初次登记。",
            payload={"layer": payload.layer.value},
        )
        return self.registry.save(case)

    def list_cases(self) -> list[CaseRecord]:
        return self.registry.list()

    def get_case(self, case_id: str) -> CaseRecord:
        return self.registry.get(case_id)

    def get_timeline(self, case_id: str) -> list[dict]:
        return export_timeline(self.get_case(case_id))

    def get_dossier(self, case_id: str) -> dict:
        return export_case_dossier(self.get_case(case_id))

    def accept_case(self, case_id: str, actor: str) -> CaseRecord:
        case = self.get_case(case_id)
        return self._transition(case, CaseStatus.ACCEPTED, actor, "case_accepted", "案件已受理。")

    def submit_for_approval(self, case_id: str, actor: str) -> CaseRecord:
        case = self.get_case(case_id)
        if case.status == CaseStatus.ACCEPTED:
            case = self._transition(case, CaseStatus.PLANNING, actor, "planning_started", "内阁开始票拟。")
        if case.status == CaseStatus.PLANNING:
            case = self._transition(
                case,
                CaseStatus.INTERNAL_REVIEW,
                actor,
                "internal_review_started",
                "进入内部复核与材料整理。",
            )
        return self._transition(
            case,
            CaseStatus.SUBMITTED_FOR_APPROVAL,
            actor,
            "submitted_for_approval",
            "方案已提交司礼监审批。",
        )

    def approve_case(self, case_id: str, actor: str) -> CaseRecord:
        case = self.get_case(case_id)
        return self._transition(case, CaseStatus.APPROVED, actor, "case_approved", "审批通过。")

    def reject_case(self, case_id: str, request: ActionRequest) -> CaseRecord:
        case = self.get_case(case_id)
        message = request.reason or "方案被正式封驳，需返工。"
        return self._transition(case, CaseStatus.REJECTED, request.actor, "case_rejected", message)

    def dispatch_case(self, case_id: str, actor: str) -> CaseRecord:
        case = self.get_case(case_id)
        return self._transition(case, CaseStatus.DISPATCHED, actor, "case_dispatched", "任务已下达到执行链。")

    def start_execution(self, case_id: str, actor: str) -> CaseRecord:
        case = self.get_case(case_id)
        return self._transition(case, CaseStatus.EXECUTING, actor, "execution_started", "进入执行阶段。")

    def mark_reporting(self, case_id: str, actor: str) -> CaseRecord:
        case = self.get_case(case_id)
        return self._transition(case, CaseStatus.REPORTING, actor, "reporting_started", "进入回奏整理阶段。")

    def archive_case(self, case_id: str, actor: str) -> CaseRecord:
        case = self.get_case(case_id)
        return self._transition(case, CaseStatus.ARCHIVED, actor, "case_archived", "案件归档完成。")

    def mark_repair_pending(self, case_id: str, request: ActionRequest) -> CaseRecord:
        case = self.get_case(case_id)
        message = request.reason or "检测到异常，等待老板/董事会修复令。"
        return self._transition(
            case,
            CaseStatus.REPAIR_PENDING,
            request.actor,
            "repair_pending",
            message,
            payload={"reported_by": request.actor},
        )

    def authorize_repair(self, case_id: str, request: RepairOrderRequest) -> CaseRecord:
        case = self.get_case(case_id)
        case.metadata.setdefault("repair_chain", []).append(
            {
                "strategy": request.strategy,
                "reason": request.reason,
                "scope": request.scope,
                "authorized_by": request.actor,
            }
        )
        return self._transition(
            case,
            CaseStatus.REPAIR_AUTHORIZED,
            request.actor,
            "repair_authorized",
            "修复令已下达，可进入逐级执行。",
            payload={
                "strategy": request.strategy,
                "reason": request.reason,
                "scope": request.scope,
            },
        )

    def rerun_case(self, case_id: str, actor: str) -> CaseRecord:
        case = self.get_case(case_id)
        return self._transition(case, CaseStatus.RERUNNING, actor, "case_rerunning", "接令后开始重跑。")

    def pause_case(self, case_id: str, request: ActionRequest) -> CaseRecord:
        case = self.get_case(case_id)
        if is_terminal(case.status) or case.status == CaseStatus.PAUSED:
            raise ValueError(f"case cannot be paused from {case.status.value}")
        case.metadata["paused_from"] = case.status.value
        return self._transition(
            case,
            CaseStatus.PAUSED,
            request.actor,
            "case_paused",
            request.reason or "案件已暂停。",
        )

    def resume_case(self, case_id: str, request: ActionRequest) -> CaseRecord:
        case = self.get_case(case_id)
        if case.status != CaseStatus.PAUSED:
            raise ValueError("only paused cases can be resumed")
        previous_status = case.metadata.pop("paused_from", CaseStatus.ACCEPTED.value)
        target = CaseStatus(previous_status)
        return self._transition(
            case,
            target,
            request.actor,
            "case_resumed",
            request.reason or f"案件从暂停恢复到 {target.value}。",
            validate=False,
        )

    def freeze_case(self, case_id: str, request: ActionRequest) -> CaseRecord:
        case = self.get_case(case_id)
        if is_terminal(case.status):
            raise ValueError(f"case cannot be frozen from {case.status.value}")
        case.metadata["frozen_from"] = case.status.value
        return self._transition(
            case,
            CaseStatus.FROZEN,
            request.actor,
            "case_frozen",
            request.reason or "案件已冻结，等待进一步处置。",
        )

    def cancel_case(self, case_id: str, request: ActionRequest) -> CaseRecord:
        case = self.get_case(case_id)
        if is_terminal(case.status):
            raise ValueError(f"case cannot be cancelled from {case.status.value}")
        return self._transition(
            case,
            CaseStatus.CANCELLED,
            request.actor,
            "case_cancelled",
            request.reason or "案件已取消。",
        )

    def list_agents(self) -> list[AgentProfile]:
        return AGENT_CATALOG

    def runtime_capabilities(self) -> list[RuntimeCapability]:
        return RUNTIME_CAPABILITIES

    def _transition(
        self,
        case: CaseRecord,
        target: CaseStatus,
        actor: str,
        event_type: str,
        message: str,
        payload: dict | None = None,
        *,
        validate: bool = True,
    ) -> CaseRecord:
        if validate:
            assert_transition(case.status, target)
        from_status = case.status
        case.status = target
        self._append_event(
            case,
            event_type=event_type,
            actor=actor,
            from_status=from_status,
            to_status=target,
            message=message,
            payload=payload or {},
        )
        return self.registry.save(case)

    def _append_event(
        self,
        case: CaseRecord,
        event_type: str,
        actor: str,
        from_status: CaseStatus | None,
        to_status: CaseStatus | None,
        message: str,
        payload: dict,
    ) -> None:
        event = TimelineEvent(
            event_id=f"evt_{uuid4().hex[:12]}",
            event_type=event_type,
            actor=actor,
            from_status=from_status,
            to_status=to_status,
            message=message,
            payload=payload,
        )
        case.timeline.append(event)
        self.event_bus.publish(
            GovernanceEvent(
                name=event_type,
                case_id=case.case_id,
                actor=actor,
                data=event.model_dump(mode="json"),
            )
        )

