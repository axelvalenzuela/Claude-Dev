from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from expenses.history_export import build_history_document
from expenses.models import ExpenseReport, ExpenseReportAuditLog, log_action

TODAY = timezone.now().date()


class HistoryExportTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="x", first_name="Ana Perez"
        )
        self.admin = User.objects.create_user(
            username="admin@example.com", email="admin@example.com", password="x", first_name="HR Admin"
        )
        self.report = ExpenseReport.objects.create(user=self.employee, title="Trip to Puebla")

    def _all_text(self, document):
        parts = [p.text for p in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    parts.append(cell.text)
        return "\n".join(parts)

    def test_includes_every_audit_log_entry_in_chronological_order(self):
        log_action(self.report, self.employee, ExpenseReportAuditLog.Action.SUBMITTED)
        log_action(self.report, self.admin, ExpenseReportAuditLog.Action.REJECTED, "Missing receipt")
        log_action(self.report, self.employee, ExpenseReportAuditLog.Action.SUBMITTED)
        log_action(self.report, self.admin, ExpenseReportAuditLog.Action.APPROVED, "Looks good now")

        document = build_history_document(self.report)
        text = self._all_text(document)

        self.assertIn("Ana Perez", text)
        self.assertIn("Missing receipt", text)
        self.assertIn("Looks good now", text)
        self.assertIn("Rejected", text)
        self.assertIn("Approved", text)

        # "Rejected" (from the first reject) must appear before "Looks good
        # now" (the later approval note) — chronological, not newest-first.
        self.assertLess(text.index("Missing receipt"), text.index("Looks good now"))

    def test_entry_with_no_actor_shows_system(self):
        log_action(self.report, None, ExpenseReportAuditLog.Action.DOCUMENT_DELETED, "retention cleanup")
        document = build_history_document(self.report)
        self.assertIn("System", self._all_text(document))

    def test_no_audit_log_entries_still_produces_a_document(self):
        document = build_history_document(self.report)
        self.assertGreaterEqual(len(document.paragraphs) + len(document.tables), 1)
