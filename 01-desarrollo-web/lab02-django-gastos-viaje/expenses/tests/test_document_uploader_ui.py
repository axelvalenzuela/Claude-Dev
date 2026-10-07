"""The drag-and-drop, multi-file, live-preview uploader (static/js/
document-uploader.js, expenses/templates/expenses/_document_uploader.html)
is shared between the New Report page and a draft report's own detail
page — added so adding one more receipt to an existing draft doesn't fall
back to the old single-file, full-page-reload form. The uploader's own
drag/drop/preview behavior is client-side JS and isn't exercised here;
what these tests cover is that both pages actually render the shared
component (not two diverging copies) and that the view context it needs
(doc_types) is present."""
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from expenses.models import ExpenseReport, TravelDocument


class SharedUploaderRendersOnBothPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )
        self.client.login(username="ana@example.com", password="clave123")

    def test_new_report_page_renders_the_shared_uploader(self):
        response = self.client.get(reverse("reports:create"))
        self.assertContains(response, 'id="file-drop-zone"')
        self.assertContains(response, 'id="document-tab-button-template"')
        self.assertContains(response, "document-uploader.js")

    def test_draft_report_detail_page_renders_the_shared_uploader(self):
        report = ExpenseReport.objects.create(user=self.user, title="Trip", supervisor_name="Someone")
        response = self.client.get(reverse("reports:detail", args=[report.pk]))
        self.assertContains(response, 'id="file-drop-zone"')
        self.assertContains(response, 'id="document-tab-button-template"')
        self.assertContains(response, "document-uploader.js")

    def test_submitted_report_detail_page_does_not_render_the_uploader(self):
        # Only draft reports can still have documents added — the
        # uploader (and its script) has no reason to load once that's
        # no longer possible.
        report = ExpenseReport.objects.create(user=self.user, title="Trip", supervisor_name="Someone")
        report.status = ExpenseReport.Status.SUBMITTED
        report.save()

        response = self.client.get(reverse("reports:detail", args=[report.pk]))

        self.assertNotContains(response, 'id="file-drop-zone"')
        self.assertNotContains(response, "document-uploader.js")

    def test_detail_view_context_has_doc_types_for_the_uploader(self):
        report = ExpenseReport.objects.create(user=self.user, title="Trip", supervisor_name="Someone")
        response = self.client.get(reverse("reports:detail", args=[report.pk]))
        self.assertEqual(list(response.context["doc_types"]), list(TravelDocument.DocType.choices))
