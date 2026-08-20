"""Data migration: the TravelDocument.type choices used to be in Spanish
(vuelo/transporte/alimentos/otro). Remap any existing rows to the new
English values (flight/taxi/meal/other) so old data keeps working."""
from django.db import migrations

LEGACY_TO_NEW = {
    "vuelo": "flight",
    "transporte": "taxi",
    "alimentos": "meal",
    "otro": "other",
}


def remap_forward(apps, schema_editor):
    TravelDocument = apps.get_model("expenses", "TravelDocument")
    for old_value, new_value in LEGACY_TO_NEW.items():
        TravelDocument.objects.filter(type=old_value).update(type=new_value)
        TravelDocument.objects.filter(detected_type=old_value).update(detected_type=new_value)


def remap_backward(apps, schema_editor):
    TravelDocument = apps.get_model("expenses", "TravelDocument")
    for old_value, new_value in LEGACY_TO_NEW.items():
        TravelDocument.objects.filter(type=new_value).update(type=old_value)
        TravelDocument.objects.filter(detected_type=new_value).update(detected_type=old_value)


class Migration(migrations.Migration):
    dependencies = [("expenses", "0003_expensereport_approval_clause_and_more")]
    operations = [migrations.RunPython(remap_forward, remap_backward)]
