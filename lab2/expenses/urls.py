from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_list, name="list"),
    path("new/", views.report_create, name="create"),
    path("<int:pk>/", views.report_detail, name="detail"),
    path("<int:pk>/upload/", views.upload_document, name="upload_document"),
    path("<int:pk>/documents/<int:doc_id>/delete/", views.delete_document, name="delete_document"),
    path("<int:pk>/documents/<int:doc_id>/download/", views.download_document, name="download_document"),
    path("<int:pk>/submit/", views.submit_report, name="submit"),
    path("<int:pk>/export/", views.export_excel, name="export_excel"),
]
