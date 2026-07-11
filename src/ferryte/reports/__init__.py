"""Coverage + blind-spot reports and rendering."""

from .audit import AuditMeta, write_audit_report
from .coverage import CoverageReport, build_coverage_report
from .render import (
    render_blindspots_table,
    render_coverage_table,
    render_results_table,
    write_html_report,
    write_json_report,
)

__all__ = [
    "AuditMeta",
    "CoverageReport",
    "build_coverage_report",
    "render_results_table",
    "render_coverage_table",
    "render_blindspots_table",
    "write_json_report",
    "write_html_report",
    "write_audit_report",
]
