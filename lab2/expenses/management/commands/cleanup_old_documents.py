"""Enforces the file retention policy (expenses/policies.py:FILE_RETENTION_
DAYS): deletes the original file of any TravelDocument uploaded more than
that many days ago, regardless of the report's status. The TravelDocument
row itself, and the ExpenseReport it belongs to, are never touched — only
the file, exactly like approval already does (services.finalize_approval)
for a report that's been decided on. This is what actually reclaims space
for a report that never got acted on (still `submitted`) or was rejected
(which, unlike approval, doesn't already delete originals — see
services.py's docstring on why).

Not run automatically by the app itself — schedule it (cron on Linux,
Task Scheduler on Windows) per docs/DEPLOYMENT.md. Safe to run as often as
you like; a document with no file, or one uploaded within the retention
window, is simply skipped.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from expenses.models import ExpenseReportAuditLog, TravelDocument, log_action
from expenses.policies import FILE_RETENTION_DAYS


class Command(BaseCommand):
    help = f"Deletes original receipt files older than {FILE_RETENTION_DAYS} days (retention policy)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List what would be deleted without actually deleting anything.",
        )

    def handle(self, *args, dry_run=False, **options):
        cutoff = timezone.now() - timezone.timedelta(days=FILE_RETENTION_DAYS)
        stale_documents = TravelDocument.objects.exclude(file="").filter(uploaded_at__lt=cutoff)

        count = 0
        for document in stale_documents:
            self.stdout.write(
                f"{'Would delete' if dry_run else 'Deleting'}: "
                f"{document.file_name} (report #{document.expense_report_id}, "
                f"uploaded {document.uploaded_at:%Y-%m-%d})"
            )
            if not dry_run:
                document.file.delete(save=False)
                document.file = None
                document.save(update_fields=["file"])
                log_action(
                    document.expense_report,
                    None,
                    ExpenseReportAuditLog.Action.DOCUMENT_DELETED,
                    f"Original file removed automatically after {FILE_RETENTION_DAYS}-day retention period.",
                )
            count += 1

        verb = "Would remove" if dry_run else "Removed"
        self.stdout.write(self.style.SUCCESS(f"{verb} {count} file(s) older than {FILE_RETENTION_DAYS} days."))
