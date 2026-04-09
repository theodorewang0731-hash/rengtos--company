from __future__ import annotations

from core.models import CaseRecord


def export_timeline(case: CaseRecord) -> list[dict]:
    return [event.model_dump(mode="json") for event in case.timeline]


def export_case_dossier(case: CaseRecord) -> dict:
    return {
        "case": case.model_dump(mode="json", exclude={"timeline"}),
        "timeline": export_timeline(case),
    }

