from django.urls import path
from .views import TextProcessingView, get_processed_texts_by_id, docs, openapi_file, upload_reference_samples, upload_success

urlpatterns = [
    path("process/", TextProcessingView.as_view(), name="process"),
    path("processed/", get_processed_texts_by_id, name="processed"),
    path("swagger/", docs, name="swagger"),
    path("openapi.yaml/", openapi_file, name="bruh"),
    path("upload/", upload_reference_samples, name="upload-table"),
    path("upload-success/", upload_success, name="upload-success"),
]
