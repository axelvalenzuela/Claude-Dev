"""Local-dev safety net: automatically stop `manage.py runserver` after a
fixed number of hours (AUTO_SHUTDOWN_HOURS in settings, default 12), so a
server someone forgot to stop doesn't keep running on their machine
indefinitely. This never applies to anything other than `runserver` — tests,
migrations, shell sessions, etc. are all unaffected.
"""
import os
import sys
import threading

from django.conf import settings


def start_auto_shutdown_timer():
    """Arms a background timer that terminates this process once
    AUTO_SHUTDOWN_HOURS has elapsed. Safe to call on every app startup: it
    no-ops unless the current process is the one actually serving
    `runserver` requests.
    """
    hours = getattr(settings, "AUTO_SHUTDOWN_HOURS", 0)
    if not hours or hours <= 0:
        return

    if not _is_the_serving_runserver_process():
        return

    seconds = hours * 3600
    timer = threading.Timer(seconds, _shutdown, args=(hours,))
    # A daemon thread so it never blocks the interpreter from exiting on its own.
    timer.daemon = True
    timer.start()


def _is_the_serving_runserver_process() -> bool:
    """`manage.py runserver` (without --noreload) launches a child process
    to actually serve requests, keeping the original process as a
    file-watcher that restarts it on code changes. Both processes import
    settings and call this function, but only the child sets RUN_MAIN=true.
    With --noreload there's no child process at all, so there's nothing to
    disambiguate. Either way, this returns True exactly once per server
    that's actually listening for requests — never for `test`, `migrate`,
    `shell`, etc."""
    if "runserver" not in sys.argv:
        return False
    return os.environ.get("RUN_MAIN") == "true" or "--noreload" in sys.argv


def _shutdown(hours: float) -> None:
    print(
        f"\n[MHP Expense Reports] Local dev server auto-shutdown: "
        f"the {hours:g}-hour limit has been reached. Stopping.\n"
        f"Run `python manage.py runserver` again to start a new session.\n"
    )
    # A background thread can't cleanly ask the WSGI server's main thread to
    # stop; terminating the process outright is the standard way to end a
    # `runserver` session from outside its request-handling loop.
    os._exit(0)
