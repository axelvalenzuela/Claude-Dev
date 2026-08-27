"""Prunes BlacklistedToken rows (accounts/jwt_auth.py) past their own
expires_at. A blacklist row exists only to reject a refresh token before
its natural expiry (see accounts/models.py:BlacklistedToken); once that
expiry has passed, the token would already fail validation on its own
`exp` claim regardless of the blacklist, so keeping the row any longer is
just clutter, not a security requirement.

Not run automatically by the app itself — schedule it (cron on Linux,
Task Scheduler on Windows) alongside cleanup_old_documents, per
docs/DEPLOYMENT.md."""
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import BlacklistedToken


class Command(BaseCommand):
    help = "Deletes BlacklistedToken rows whose refresh token has already expired on its own."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many rows would be deleted without actually deleting anything.",
        )

    def handle(self, *args, dry_run=False, **options):
        expired = BlacklistedToken.objects.filter(expires_at__lt=timezone.now())
        count = expired.count()

        if dry_run:
            self.stdout.write(f"Would remove {count} expired blacklisted token(s).")
            return

        expired.delete()
        self.stdout.write(self.style.SUCCESS(f"Removed {count} expired blacklisted token(s)."))
