"""The floating help-chat widget: the rule-based answer engine
(accounts/faq.py) and its three per-account-scoped endpoints
(accounts/help_chat_views.py) — history, ask, reset."""
import json

from django.test import TestCase
from django.urls import reverse

from accounts.faq import FALLBACK_ANSWER, find_answer
from accounts.models import HelpChatMessage, User


class FindAnswerTests(TestCase):
    def test_matches_an_employee_question_by_keyword(self):
        answer = find_answer("how do I attach a receipt?", is_staff=False)
        self.assertIn("Drag files", answer)

    def test_matches_an_admin_question_by_keyword(self):
        answer = find_answer("how do I approve a report", is_staff=True)
        self.assertIn("Review tab", answer)

    def test_admin_only_entry_is_invisible_to_an_employee(self):
        # "grant admin access" keywords shouldn't surface for a regular
        # employee even if their wording happens to overlap.
        answer = find_answer("how do I get admin access users groups", is_staff=False)
        self.assertNotIn("is_superuser", answer)

    def test_employee_only_entry_is_invisible_to_an_admin(self):
        # None of these keywords overlap any "all"/"admin" entry, so an
        # admin asking this gets the fallback, not the employee-only
        # "How do I create a new expense report?" answer.
        answer = find_answer("how do I create a new report", is_staff=True)
        self.assertEqual(answer, FALLBACK_ANSWER)

    def test_shared_entry_answers_both_roles(self):
        employee_answer = find_answer("what is the 60 dollar policy", is_staff=False)
        admin_answer = find_answer("what is the 60 dollar policy", is_staff=True)
        self.assertEqual(employee_answer, admin_answer)
        self.assertIn("$60", employee_answer)

    def test_unmatched_question_returns_the_fallback(self):
        self.assertEqual(find_answer("asdkjhaskjdh gibberish", is_staff=False), FALLBACK_ANSWER)

    def test_empty_message_returns_the_fallback(self):
        self.assertEqual(find_answer("", is_staff=False), FALLBACK_ANSWER)


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
