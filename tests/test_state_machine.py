import pytest

from core.models import CaseStatus
from core.state_machine import assert_transition, transition_matrix


def test_allows_valid_transition() -> None:
    assert_transition(CaseStatus.CREATED, CaseStatus.ACCEPTED)


def test_rejects_invalid_transition() -> None:
    with pytest.raises(ValueError):
        assert_transition(CaseStatus.CREATED, CaseStatus.APPROVED)


def test_transition_matrix_contains_main_flow() -> None:
    matrix = transition_matrix()
    assert "accepted" in matrix["created"]
    assert "submitted_for_approval" in matrix["planning"]
