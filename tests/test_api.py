from fastapi.testclient import TestClient

from apps.api.main import app, event_bus, registry


client = TestClient(app)


def setup_function() -> None:
    registry.clear()
    event_bus.clear()


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_case_flow_and_repair_chain() -> None:
    create_response = client.post(
        "/api/cases",
        json={
            "title": "治理测试案件",
            "content": "验证最小案件流转与修复受令闭环",
            "priority": "high",
            "submitted_by": "tester",
        },
    )
    assert create_response.status_code == 201
    case_id = create_response.json()["case_id"]

    assert client.post(f"/api/cases/{case_id}/accept").status_code == 200
    submitted = client.post(f"/api/cases/{case_id}/submit-for-approval")
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "submitted_for_approval"

    assert client.post(f"/api/cases/{case_id}/approve").status_code == 200
    assert client.post(f"/api/cases/{case_id}/dispatch").status_code == 200
    assert client.post(f"/api/cases/{case_id}/start-execution").status_code == 200

    repair_pending = client.post(
        f"/api/cases/{case_id}/repair-pending",
        json={"reason": "dependency corruption", "actor": "jinyiwei"},
    )
    assert repair_pending.status_code == 200
    assert repair_pending.json()["status"] == "repair_pending"

    repair_order = client.post(
        f"/api/cases/{case_id}/repair-order",
        json={
            "strategy": "patch_then_rerun",
            "reason": "critical dependency issue",
            "scope": "executor_pool/api_builder",
            "actor": "board_authority",
        },
    )
    assert repair_order.status_code == 200
    assert repair_order.json()["status"] == "repair_authorized"

    rerun = client.post(f"/api/cases/{case_id}/rerun")
    assert rerun.status_code == 200
    assert rerun.json()["status"] == "rerunning"

    timeline = client.get(f"/api/cases/{case_id}/timeline")
    assert timeline.status_code == 200
    statuses = [item["to_status"] for item in timeline.json() if item["to_status"]]
    assert "planning" in statuses
    assert "internal_review" in statuses
    assert "repair_authorized" in statuses


def test_permissions_endpoint() -> None:
    response = client.get("/api/governance/permissions")
    assert response.status_code == 200
    body = response.json()
    assert body["company_manager"]["scope"] == "owned_business_line_scope"

