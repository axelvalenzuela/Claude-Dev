from django import forms

from .models import ExpenseReport, TravelDocument


class ExpenseReportForm(forms.ModelForm):
    class Meta:
        model = ExpenseReport
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Viaje a CDMX - agosto 2026"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class TravelDocumentForm(forms.ModelForm):
    class Meta:
        model = TravelDocument
        fields = ["type", "document_date", "amount", "file"]
        widgets = {
            "type": forms.Select(attrs={"class": "form-select"}),
            "document_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png"}),
        }
