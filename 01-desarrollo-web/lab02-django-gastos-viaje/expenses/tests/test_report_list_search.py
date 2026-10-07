"""The "My reports" search box (report_list.html) — same client-side
filter pattern as the admin dashboard's Employees tab search. Only shown
once there are enough reports that scrolling to find one stops being
instant; below that it would just be another control in the way."""
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from expenses.models import ExpenseReport


class ReportListSearchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )
        self.client.login(username="ana@example.com", password="clave123")

    def test_search_box_hidden_with_five_or_fewer_reports(self):
        for i in range(5):
            ExpenseReport.objects.create(user=self.user, title=f"Trip {i}", supervisor_name="Someone")

        response = self.client.get(reverse("reports:list"))

        self.assertNotContains(response, 'id="report-search"')

    def test_search_box_shown_past_five_reports(self):
        for i in range(6):
            ExpenseReport.objects.create(user=self.user, title=f"Trip {i}", supervisor_name="Someone")

        response = self.client.get(reverse("reports:list"))

        self.assertContains(response, 'id="report-search"')

    def test_each_row_carries_a_search_attribute_with_title_and_status(self):
        for i in range(6):
            ExpenseReport.objects.create(user=self.user, title=f"Puebla trip {i}", supervisor_name="Someone")

        response = self.client.get(reverse("reports:list"))

        self.assertContains(response, 'data-search="Puebla trip 0 draft"')
