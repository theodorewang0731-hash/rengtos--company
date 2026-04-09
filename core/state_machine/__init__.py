from __future__ import annotations

from core.models import CaseStatus


TERMINAL_STATUSES = {
    CaseStatus.ARCHIVED,
    CaseStatus.CANCELLED,
    CaseStatus.FROZEN,
}

ALLOWED_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.CREATED: {CaseStatus.ACCEPTED, CaseStatus.CANCELLED, CaseStatus.FROZEN},
    CaseStatus.ACCEPTED: {
        CaseStatus.PLANNING,
        CaseStatus.SUBMITTED_FOR_APPROVAL,
        CaseStatus.PAUSED,
        CaseStatus.CANCELLED,
        CaseStatus.FROZEN,
    },
    CaseStatus.PLANNING: {
        CaseStatus.INTERNAL_REVIEW,
        CaseStatus.SUBMITTED_FOR_APPROVAL,
        CaseStatus.PAUSED,
        CaseStatus.CANCELLED,
        CaseStatus.FROZEN,
    },
    CaseStatus.INTERNAL_REVIEW: {
        CaseStatus.SUBMITTED_FOR_APPROVAL,
        CaseStatus.REJECTED,
        CaseStatus.PAUSED,
        CaseStatus.FROZEN,
    },
    CaseStatus.SUBMITTED_FOR_APPROVAL: {
        CaseStatus.APPROVED,
        CaseStatus.REJECTED,
        CaseStatus.ESCALATED,
        CaseStatus.PAUSED,
        CaseStatus.FROZEN,
    },
    CaseStatus.APPROVED: {
        CaseStatus.DISPATCHED,
        CaseStatus.REPAIR_PENDING,
        CaseStatus.PAUSED,
        CaseStatus.CANCELLED,
        CaseStatus.FROZEN,
    },
    CaseStatus.REJECTED: {
        CaseStatus.PLANNING,
        CaseStatus.INTERNAL_REVIEW,
        CaseStatus.CANCELLED,
    },
    CaseStatus.ESCALATED: {
        CaseStatus.DISPATCHED,
        CaseStatus.REJECTED,
        CaseStatus.CANCELLED,
        CaseStatus.FROZEN,
    },
    CaseStatus.DISPATCHED: {
        CaseStatus.EXECUTING,
        CaseStatus.REPAIR_PENDING,
        CaseStatus.PAUSED,
        CaseStatus.CANCELLED,
        CaseStatus.FROZEN,
    },
    CaseStatus.EXECUTING: {
        CaseStatus.REPORTING,
        CaseStatus.REPAIR_PENDING,
        CaseStatus.PAUSED,
        CaseStatus.CANCELLED,
        CaseStatus.FROZEN,
    },
    CaseStatus.REPORTING: {
        CaseStatus.ARCHIVED,
        CaseStatus.REPAIR_PENDING,
        CaseStatus.PAUSED,
        CaseStatus.FROZEN,
    },
    CaseStatus.REPAIR_PENDING: {
        CaseStatus.REPAIR_AUTHORIZED,
        CaseStatus.REJECTED,
        CaseStatus.PAUSED,
        CaseStatus.FROZEN,
    },
    CaseStatus.REPAIR_AUTHORIZED: {
        CaseStatus.RERUNNING,
        CaseStatus.PAUSED,
        CaseStatus.FROZEN,
    },
    CaseStatus.RERUNNING: {
        CaseStatus.EXECUTING,
        CaseStatus.REPORTING,
        CaseStatus.REPAIR_PENDING,
        CaseStatus.PAUSED,
        CaseStatus.FROZEN,
    },
    CaseStatus.PAUSED: set(),
    CaseStatus.FROZEN: set(),
    CaseStatus.CANCELLED: set(),
    CaseStatus.ARCHIVED: set(),
}


def assert_transition(current: CaseStatus, target: CaseStatus) -> None:
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"illegal transition: {current.value} -> {target.value}")


def is_terminal(status: CaseStatus) -> bool:
    return status in TERMINAL_STATUSES


def transition_matrix() -> dict[str, list[str]]:
    return {
        current.value: [target.value for target in sorted(targets, key=lambda item: item.value)]
        for current, targets in ALLOWED_TRANSITIONS.items()
    }

