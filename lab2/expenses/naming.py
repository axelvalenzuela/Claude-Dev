"""Generates the on-disk/download file name for a report's Excel/Word
exports. Kept separate from excel.py/word_export.py (which only build file
*content*) so RH's naming convention — employee name, submission date,
employee number, plus an "APROBADO" marker once approved — can change
without touching content-generation code.
"""
import re


def _sanitize(value: str) -> str:
    value = value.strip().replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9_-]", "", value) or "unknown"


def export_basename(report, *, approved: bool = False) -> str:
    employee = report.user.get_full_name() or report.user.email
    reference_date = (report.submitted_at or report.created_at).date()
    name = "_".join(
        [
            _sanitize(employee),
            reference_date.isoformat(),
            report.user.employee_number or "SINNUM",
        ]
    )
    return f"{name}_APROBADO" if approved else name
