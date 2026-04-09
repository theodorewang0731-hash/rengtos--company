from __future__ import annotations

from uuid import uuid4

from core.models import CaseRecord, CreateCaseRequest, utc_now


class CaseRegistry:
    def __init__(self) -> None:
        self._cases: dict[str, CaseRecord] = {}

    def create(self, payload: CreateCaseRequest) -> CaseRecord:
        case_id = f"case_{uuid4().hex[:12]}"
        case = CaseRecord(
            case_id=case_id,
            title=payload.title,
            content=payload.content,
            priority=payload.priority,
            submitted_by=payload.submitted_by,
            layer=payload.layer,
            metadata=dict(payload.metadata),
        )
        self._cases[case_id] = case
        return case

    def get(self, case_id: str) -> CaseRecord:
        try:
            return self._cases[case_id]
        except KeyError as exc:
            raise KeyError(f"case '{case_id}' does not exist") from exc

    def save(self, case: CaseRecord) -> CaseRecord:
        case.updated_at = utc_now()
        self._cases[case.case_id] = case
        return case

    def list(self) -> list[CaseRecord]:
        return sorted(self._cases.values(), key=lambda item: item.created_at)

    def clear(self) -> None:
        self._cases.clear()

