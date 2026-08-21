"""Tests for the 12-hour local dev server auto-shutdown guard logic.

These only check *whether the timer would be armed* for a given process —
they never actually wait for (or trigger) a real shutdown, since that would
require sleeping for hours or mocking os._exit in a way that's more trouble
than it's worth for a dev-convenience feature.
"""
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from accounts.server_lifecycle import _is_the_serving_runserver_process, start_auto_shutdown_timer


class ServingProcessDetectionTests(SimpleTestCase):
    def test_not_runserver_never_matches(self):
        with patch("sys.argv", ["manage.py", "test"]):
            self.assertFalse(_is_the_serving_runserver_process())

    def test_runserver_with_noreload_matches(self):
        with patch("sys.argv", ["manage.py", "runserver", "--noreload"]):
            self.assertTrue(_is_the_serving_runserver_process())

    def test_runserver_without_run_main_or_noreload_does_not_match(self):
        # This is the autoreloader's parent/watcher process — it must NOT
        # start a timer, or the server would get two competing shutdowns.
        with patch("sys.argv", ["manage.py", "runserver"]), patch.dict("os.environ", {}, clear=True):
            self.assertFalse(_is_the_serving_runserver_process())

    def test_runserver_child_process_with_run_main_matches(self):
        with patch("sys.argv", ["manage.py", "runserver"]), patch.dict("os.environ", {"RUN_MAIN": "true"}):
            self.assertTrue(_is_the_serving_runserver_process())


class StartAutoShutdownTimerTests(SimpleTestCase):
    @override_settings(AUTO_SHUTDOWN_HOURS=0)
    def test_disabled_when_hours_is_zero(self):
        with patch("threading.Timer") as mock_timer:
            start_auto_shutdown_timer()
        mock_timer.assert_not_called()

    @override_settings(AUTO_SHUTDOWN_HOURS=12)
    def test_not_armed_outside_of_runserver(self):
        with patch("sys.argv", ["manage.py", "test"]), patch("threading.Timer") as mock_timer:
            start_auto_shutdown_timer()
        mock_timer.assert_not_called()

    @override_settings(AUTO_SHUTDOWN_HOURS=12)
    def test_armed_for_twelve_hours_when_serving(self):
        with patch("sys.argv", ["manage.py", "runserver", "--noreload"]), patch("threading.Timer") as mock_timer:
            start_auto_shutdown_timer()

        mock_timer.assert_called_once()
        seconds_argument = mock_timer.call_args[0][0]
        self.assertEqual(seconds_argument, 12 * 3600)
        mock_timer.return_value.start.assert_called_once()
