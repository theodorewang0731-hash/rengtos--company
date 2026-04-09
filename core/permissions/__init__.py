from __future__ import annotations


PERMISSION_MATRIX = {
    "employee": {
        "scope": "self_only",
        "can_view": ["personal_cases", "personal_issue_files"],
        "cannot_view": ["peer_issue_files", "department_dossiers", "company_wide_queries"],
    },
    "department_manager": {
        "scope": "owned_department_scope",
        "can_view": ["department_cases_in_charge", "department_issue_levels_l2_l3"],
        "cannot_view": ["other_departments", "company_wide_queries", "unowned_business_lines"],
    },
    "company_manager": {
        "scope": "owned_business_line_scope",
        "can_view": ["authorized_department_archives", "company_cases_in_charge"],
        "cannot_view": ["unowned_departments", "cross_line_open_search"],
    },
    "jinyiwei": {
        "scope": "supervised_investigation_scope",
        "can_view": ["investigation_context", "risk_archives", "upgrade_paths"],
        "cannot_view": ["open_browse_for_any_purpose"],
    },
    "owner_board": {
        "scope": "global",
        "can_view": ["all_layers", "all_departments", "all_employees", "full_repair_history"],
        "cannot_view": [],
    },
}


def get_permission_matrix() -> dict[str, dict[str, list[str] | str]]:
    return PERMISSION_MATRIX

