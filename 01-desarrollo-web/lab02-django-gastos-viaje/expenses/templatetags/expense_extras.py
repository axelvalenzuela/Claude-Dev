"""Template filters shared by the admin's review templates."""
from django import template
from django.utils.html import format_html

from ..admin.mixins import STATUS_BADGES

register = template.Library()


@register.filter
def status_pill(status: str):
    """Same colored, iconed pill as ExpenseReportAdmin's status_badge
    (list_display), usable from a plain template — status needs to be
    readable at a glance everywhere a report's state is shown, not just on
    the changelist."""
    color, label = STATUS_BADGES.get(status, ("#6c757d", status))
    return format_html(
        '<span class="status-pill status-pill-{}" style="background-color:{};">{}</span>',
        status, color, label,
    )
