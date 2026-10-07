"""The admin change form for approving/rejecting a report."""
from django import forms

from ..models import ExpenseReport
from ..policies import CEO_NAME, CEO_TITLE


class ExpenseReportAdminForm(forms.ModelForm):
    """Validates, in the admin form itself, that a status change is legal:
    only a 'Submitted' report can be approved/rejected, rejecting requires a
    note, and approving requires ticking the CEO approval clause."""

    ceo_clause_ack = forms.BooleanField(
        required=False,
        label=f"I confirm this approval is issued under the authority of {CEO_NAME} ({CEO_TITLE})",
        help_text="Required to approve a report. Not needed to reject one.",
    )

    class Meta:
        model = ExpenseReport
        fields = ["status", "review_note", "ceo_clause_ack"]

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            return cleaned_data

        current_status = ExpenseReport.objects.get(pk=self.instance.pk).status
        new_status = cleaned_data.get("status")
        note = cleaned_data.get("review_note") or ""

        if new_status == current_status:
            return cleaned_data

        if current_status != ExpenseReport.Status.SUBMITTED:
            raise forms.ValidationError("You can only approve or reject a report that is 'Submitted'.")
        if new_status not in (ExpenseReport.Status.APPROVED, ExpenseReport.Status.REJECTED):
            raise forms.ValidationError("From here you can only change the status to Approved or Rejected.")
        if new_status == ExpenseReport.Status.REJECTED and not note.strip():
            raise forms.ValidationError("You must provide a note/reason to reject the report.")
        if new_status == ExpenseReport.Status.APPROVED and not cleaned_data.get("ceo_clause_ack"):
            raise forms.ValidationError(
                f"You must confirm the CEO approval clause ({CEO_NAME}, {CEO_TITLE}) before approving."
            )

        return cleaned_data
