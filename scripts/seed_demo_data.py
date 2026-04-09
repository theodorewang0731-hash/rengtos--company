from __future__ import annotations

import argparse

import httpx


def request(client: httpx.Client, method: str, path: str, payload: dict | None = None) -> dict:
    response = client.request(method, path, json=payload)
    response.raise_for_status()
    return response.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data into a running RegentOS API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL for the RegentOS API.")
    args = parser.parse_args()

    cases = [
        {
            "title": "企业知识库系统设计",
            "content": "FastAPI + PostgreSQL + 全文搜索 + 权限分级",
            "priority": "high",
            "submitted_by": "imperial_user",
        },
        {
            "title": "跨部门活动复盘",
            "content": "梳理市场、销售、客服三方问题链并形成回奏稿",
            "priority": "medium",
            "submitted_by": "ops_lead",
            "layer": "department",
        },
    ]

    with httpx.Client(base_url=args.base_url, timeout=10.0) as client:
        for payload in cases:
            case = request(client, "POST", "/api/cases", payload)
            case_id = case["case_id"]
            request(client, "POST", f"/api/cases/{case_id}/accept")
            request(client, "POST", f"/api/cases/{case_id}/submit-for-approval")
            request(client, "POST", f"/api/cases/{case_id}/approve")
            print(f"seeded {case_id}: {payload['title']}")


if __name__ == "__main__":
    main()

