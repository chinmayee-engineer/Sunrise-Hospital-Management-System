"""Departments, used by doctors and analytics."""
from __future__ import annotations

from core.database.db import execute, next_numeric_id, query_all, query_one
from core.utils.ids import next_id


def ensure_department(name: str, description: str = "") -> str:
    row = query_one("SELECT department_id FROM departments WHERE name = ?", (name,))
    if row:
        return row["department_id"]
    department_id = next_id("department", next_numeric_id("departments", "department_id"))
    execute("INSERT INTO departments (department_id, name, description) VALUES (?, ?, ?)",
            (department_id, name, description))
    return department_id


def list_departments() -> list[dict]:
    return query_all("SELECT * FROM departments ORDER BY name ASC")
