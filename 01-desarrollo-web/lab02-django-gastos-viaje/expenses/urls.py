"""URLs for the employee-facing side of the app; the admin approval
interface lives entirely under Django Admin's own /admin/ routes instead
(see expenses/admin/)."""
from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportListView.as_view(), name="list"),
    path("history/", views.ReportHistoryView.as_view(), name="history"),
    path("new/", views.ReportCreateView.as_view(), name="create"),
    path("preview-document/", views.PreviewDocumentView.as_view(), name="preview_document"),
    path("<int:pk>/", views.ReportDetailView.as_view(), name="detail"),
    path("<int:pk>/upload/", views.UploadDocumentView.as_view(), name="upload_document"),
    path("<int:pk>/documents/<int:doc_id>/delete/", views.DeleteDocumentView.as_view(), name="delete_document"),
    path("<int:pk>/documents/<int:doc_id>/download/", views.DownloadDocumentView.as_view(), name="download_document"),
    path("<int:pk>/submit/", views.SubmitReportView.as_view(), name="submit"),
    path("<int:pk>/export/", views.ExportExcelView.as_view(), name="export_excel"),
    path("<int:pk>/export/word/", views.ExportWordView.as_view(), name="export_word"),
]
