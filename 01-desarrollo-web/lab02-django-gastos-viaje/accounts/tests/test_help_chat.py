"""The floating help-chat widget: the rule-based answer engine
(accounts/faq.py) — including the dynamic, live-data lookups (employee
number, supervisor, pending-report owners, recent activity) alongside
the fixed FAQ entries — and its three per-account-scoped endpoints
(accounts/help_chat_views.py) — history, ask, reset."""
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.faq import FALLBACK_ANSWER, find_answer
from accounts.models import HelpChatMessage, User
from expenses.models import ExpenseReport, ExpenseReportAuditLog, log_action
from expenses.policies import USD_MXN_RATE

TODAY = timezone.now().date()


class FindAnswerTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="x", employee_number="1234567"
        )
        self.admin = User.objects.get(email="iris.cortez@mhp.com")

    def test_matches_an_employee_question_by_keyword(self):
        answer = find_answer("how do I attach a receipt?", user=self.employee)
        self.assertIn("Drag files", answer)

    def test_matches_an_admin_question_by_keyword(self):
        answer = find_answer("how do I approve a report", user=self.admin)
        self.assertIn("Review tab", answer)

    def test_admin_only_entry_is_invisible_to_an_employee(self):
        # "grant admin access" keywords shouldn't surface for a regular
        # employee even if their wording happens to overlap.
        answer = find_answer("how do I get admin access users groups", user=self.employee)
        self.assertNotIn("is_superuser", answer)

    def test_employee_only_entry_is_invisible_to_an_admin(self):
        # None of these keywords overlap any "all"/"admin" entry, so an
        # admin asking this gets the fallback, not the employee-only
        # "How do I create a new expense report?" answer.
        answer = find_answer("how do I create a new report", user=self.admin)
        self.assertEqual(answer, FALLBACK_ANSWER)

    def test_shared_entry_answers_both_roles(self):
        employee_answer = find_answer("what is the 60 dollar policy", user=self.employee)
        admin_answer = find_answer("what is the 60 dollar policy", user=self.admin)
        self.assertEqual(employee_answer, admin_answer)
        self.assertIn("$60", employee_answer)

    def test_unmatched_question_returns_the_fallback(self):
        self.assertEqual(find_answer("asdkjhaskjdh gibberish", user=self.employee), FALLBACK_ANSWER)

    def test_empty_message_returns_the_fallback(self):
        self.assertEqual(find_answer("", user=self.employee), FALLBACK_ANSWER)

    def test_expense_types_are_read_from_the_model_not_hardcoded(self):
        from expenses.models import TravelDocument

        answer = find_answer("what expense types can I use", user=self.employee)
        for _, label in TravelDocument.DocType.choices:
            self.assertIn(label, answer)

    def test_currency_answer_includes_the_real_exchange_rate(self):
        answer = find_answer("what's the exchange rate for pesos", user=self.employee)
        self.assertIn(str(USD_MXN_RATE), answer)

    def test_my_employee_number_is_a_personal_dynamic_answer(self):
        answer = find_answer("what's my employee number?", user=self.employee)
        self.assertIn("1234567", answer)

    def test_employee_number_answer_differs_per_user(self):
        other = User.objects.create_user(
            username="ben@example.com", email="ben@example.com", password="x", employee_number="7654321"
        )
        self.assertIn("1234567", find_answer("my employee number", user=self.employee))
        self.assertIn("7654321", find_answer("my employee number", user=other))

    def test_who_is_my_supervisor_with_no_reports_yet(self):
        answer = find_answer("who is my supervisor", user=self.employee)
        self.assertIn("don't have a report", answer)

    def test_who_is_my_supervisor_reads_the_latest_report(self):
        ExpenseReport.objects.create(user=self.employee, title="Old trip", supervisor_name="Old Boss")
        ExpenseReport.objects.create(
            user=self.employee, title="New trip", supervisor_name="Maria Lopez", supervisor_email="maria@mhp.com"
        )
        answer = find_answer("who is my supervisor", user=self.employee)
        self.assertIn("Maria Lopez", answer)
        self.assertIn("maria@mhp.com", answer)
        self.assertNotIn("Old Boss", answer)

    def test_pending_owners_is_admin_only(self):
        # Deliberately avoids "pending" here — that word alone also
        # matches the employee-visible "track my own status" entry, which
        # would mask what this test is actually checking (that the
        # admin-only dynamic lookup itself never surfaces for an employee).
        answer = find_answer("who owns the reports", user=self.employee)
        self.assertEqual(answer, FALLBACK_ANSWER)

    def test_pending_owners_lists_submitted_report_authors(self):
        report = ExpenseReport.objects.create(user=self.employee, title="Trip", supervisor_name="S")
        report.documents.create(
            file=SimpleUploadedFile("r.jpg", b"x", content_type="image/jpeg"),
            type="hotel",
            amount="50.00",
            document_date=TODAY.isoformat(),
        )
        report.submit()
        report.save()

        answer = find_answer("who are the owners of pending reports", user=self.admin)
        # self.employee has no first/last name set, so get_full_name() falls
        # back to the email — same fallback used everywhere else in the app.
        self.assertIn("ana@example.com", answer)

    def test_pending_owners_respects_department_scope(self):
        adrian = User.objects.get(email="adrian.heymes@mhp.com")
        ics_employee = User.objects.create_user(
            username="ics@example.com", email="ics@example.com", password="x", department="ICS"
        )
        finance_employee = self.employee
        for employee, title in [(ics_employee, "ICS trip"), (finance_employee, "Finance trip")]:
            report = ExpenseReport.objects.create(user=employee, title=title, supervisor_name="S")
            report.documents.create(
                file=SimpleUploadedFile("r.jpg", b"x", content_type="image/jpeg"),
                type="hotel",
                amount="50.00",
                document_date=TODAY.isoformat(),
            )
            report.submit()
            report.save()

        answer = find_answer("who owns the pending reports", user=adrian)
        self.assertIn("ics@example.com", answer)
        self.assertNotIn("ana@example.com", answer)

    def test_recent_activity_employee_with_no_reports(self):
        answer = find_answer("what's my recent activity", user=self.employee)
        self.assertIn("No activity yet", answer)

    def test_recent_activity_employee_lists_their_own_actions(self):
        report = ExpenseReport.objects.create(user=self.employee, title="Puebla trip", supervisor_name="S")
        log_action(report, self.employee, ExpenseReportAuditLog.Action.CREATED)

        answer = find_answer("any recent activity on my reports?", user=self.employee)

        self.assertIn("Puebla trip", answer)
        self.assertIn("Created", answer)

    def test_recent_activity_employee_never_sees_another_employees_activity(self):
        other = User.objects.create_user(username="luis@example.com", email="luis@example.com", password="x")
        report = ExpenseReport.objects.create(user=other, title="Luis's trip", supervisor_name="S")
        log_action(report, other, ExpenseReportAuditLog.Action.CREATED)

        answer = find_answer("what's my recent activity", user=self.employee)

        self.assertNotIn("Luis's trip", answer)

    def test_recent_activity_is_employee_only(self):
        # Deliberately avoids "recent"/"activity" alone scoring for an
        # admin-visible entry too — this checks the employee-only lookup
        # itself never surfaces for an admin asking the employee phrasing.
        answer = find_answer("what's my recent activity", user=self.admin)
        self.assertNotIn("No activity yet", answer)

    def test_recent_activity_admin_with_nothing_in_scope(self):
        answer = find_answer("what's the recent activity lately", user=self.admin)
        self.assertIn("No recent activity", answer)

    def test_recent_activity_admin_respects_department_scope(self):
        adrian = User.objects.get(email="adrian.heymes@mhp.com")
        ics_employee = User.objects.create_user(
            username="ics2@example.com", email="ics2@example.com", password="x", department="ICS"
        )
        finance_employee = self.employee
        ics_report = ExpenseReport.objects.create(user=ics_employee, title="ICS trip", supervisor_name="S")
        log_action(ics_report, ics_employee, ExpenseReportAuditLog.Action.CREATED)
        finance_report = ExpenseReport.objects.create(user=finance_employee, title="Finance trip", supervisor_name="S")
        log_action(finance_report, finance_employee, ExpenseReportAuditLog.Action.CREATED)

        answer = find_answer("what's the recent activity", user=adrian)

        self.assertIn("ICS trip", answer)
        self.assertNotIn("Finance trip", answer)

    def test_general_overview_question_gets_a_high_level_answer(self):
        answer = find_answer("I'm lost, what is this portal for?", user=self.employee)
        self.assertIn("travel-expense-report portal", answer)


class HelpChatEndpointTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )
        self.other_employee = User.objects.create_user(
            username="ben@example.com", email="ben@example.com", password="clave123"
        )

    def test_anonymous_user_is_redirected_not_answered(self):
        response = self.client.post(
            reverse("help_chat_ask"), data=json.dumps({"message": "hi"}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 302)

    def test_ask_saves_both_messages_and_returns_an_answer(self):
        self.client.login(username="ana@example.com", password="clave123")
        response = self.client.post(
            reverse("help_chat_ask"),
            data=json.dumps({"message": "how do I attach a receipt?"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Drag files", response.json()["answer"])

        messages = list(HelpChatMessage.objects.filter(user=self.employee).order_by("created_at"))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, HelpChatMessage.Role.USER)
        self.assertEqual(messages[0].text, "how do I attach a receipt?")
        self.assertEqual(messages[1].role, HelpChatMessage.Role.BOT)

    def test_ask_rejects_an_empty_message(self):
        self.client.login(username="ana@example.com", password="clave123")
        response = self.client.post(
            reverse("help_chat_ask"), data=json.dumps({"message": "   "}), content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(HelpChatMessage.objects.count(), 0)

    def test_history_only_returns_the_requesting_users_messages(self):
        HelpChatMessage.objects.create(user=self.employee, role="user", text="mine")
        HelpChatMessage.objects.create(user=self.other_employee, role="user", text="not mine")

        self.client.login(username="ana@example.com", password="clave123")
        response = self.client.get(reverse("help_chat_history"))

        texts = [m["text"] for m in response.json()["messages"]]
        self.assertEqual(texts, ["mine"])

    def test_reset_clears_only_the_requesting_users_messages(self):
        HelpChatMessage.objects.create(user=self.employee, role="user", text="mine")
        HelpChatMessage.objects.create(user=self.other_employee, role="user", text="not mine")

        self.client.login(username="ana@example.com", password="clave123")
        response = self.client.post(reverse("help_chat_reset"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(HelpChatMessage.objects.filter(user=self.employee).count(), 0)
        self.assertEqual(HelpChatMessage.objects.filter(user=self.other_employee).count(), 1)

    def test_admin_gets_admin_scoped_answers(self):
        admin = User.objects.get(email="iris.cortez@mhp.com")
        self.client.login(username="iris.cortez@mhp.com", password="Iris#2026Local")
        response = self.client.post(
            reverse("help_chat_ask"),
            data=json.dumps({"message": "how do I approve a report"}),
            content_type="application/json",
        )
        self.assertIn("Review tab", response.json()["answer"])
        self.assertTrue(HelpChatMessage.objects.filter(user=admin).exists())


class HelpChatWidgetRenderTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )

    def test_widget_renders_on_the_employee_portal(self):
        self.client.login(username="ana@example.com", password="clave123")
        response = self.client.get(reverse("reports:list"))
        self.assertContains(response, "help-chat-widget")

    def test_widget_renders_on_the_admin(self):
        self.client.login(username="iris.cortez@mhp.com", password="Iris#2026Local")
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "help-chat-widget")

    def test_widget_is_absent_for_anonymous_visitors(self):
        response = self.client.get(reverse("login"))
        self.assertNotContains(response, "help-chat-widget")
