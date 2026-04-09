from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, Field

from core.models import utc_now


class GovernanceEvent(BaseModel):
    name: str
    case_id: str
    actor: str
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class InMemoryEventBus:
    def __init__(self) -> None:
        self._events: list[GovernanceEvent] = []
        self._subscribers: list[Callable[[GovernanceEvent], None]] = []

    def publish(self, event: GovernanceEvent) -> GovernanceEvent:
        self._events.append(event)
        for subscriber in self._subscribers:
            subscriber(event)
        return event

    def subscribe(self, callback: Callable[[GovernanceEvent], None]) -> None:
        self._subscribers.append(callback)

    def list_events(self, case_id: str | None = None) -> list[GovernanceEvent]:
        if case_id is None:
            return list(self._events)
        return [event for event in self._events if event.case_id == case_id]

    def clear(self) -> None:
        self._events.clear()

