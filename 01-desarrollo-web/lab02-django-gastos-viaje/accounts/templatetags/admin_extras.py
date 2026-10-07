"""Template filter for reorganizing the Django Admin dashboard into tabs
(see templates/admin/index.html) — splits the built-in `app_list` context
variable by app_label so "Expenses" and "Accounts/Authentication" render in
separate tab panels instead of one long stacked list on the same screen.
"""
from django import template

register = template.Library()


@register.filter
def apps_in(app_list, labels):
    """Returns only the entries of `app_list` whose app_label is one of the
    comma-separated `labels` (e.g. `app_list|apps_in:"accounts,auth"`)."""
    wanted = {label.strip() for label in labels.split(",")}
    return [app for app in app_list if app["app_label"] in wanted]
