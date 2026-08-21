"""The two employee-facing forms: creating a report, and one document on
it. TravelDocumentForm is also reused directly by expenses/services.py's
build_travel_document() for the multi-file creation path — so its
validation (extension, size, page count, all via TravelDocument.file's
field validators) runs exactly once, no matter which view is uploading."""
from django import forms

from .models import ExpenseReport, TravelDocument


class ExpenseReportForm(forms.ModelForm):
    class Meta:
        model = ExpenseReport
        fields = ["title", "description", "supervisor_name", "supervisor_email"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Mexico City trip - August 2026"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "supervisor_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Who should review this report"}),
            "supervisor_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "optional"}),
        }


class TravelDocumentForm(forms.ModelForm):
    class Meta:
        model = TravelDocument
        fields = ["type", "document_date", "amount", "currency", "vendor_name", "backup_type", "file"]
        widgets = {
            "type": forms.Select(attrs={"class": "form-select"}),
            "document_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
            "currency": forms.Select(attrs={"class": "form-select"}),
            "vendor_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. United Airlines, INC"}),
            "backup_type": forms.Select(attrs={"class": "form-select"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # `vendor_name` is blank=True at the model level (so existing rows
        # from before this field existed don't need backfilling), but every
        # new upload should still name a vendor — matches the company's
        # real Advance & Expense Report format, which never leaves it out.
        self.fields["vendor_name"].required = True
