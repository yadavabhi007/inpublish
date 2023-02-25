from django.urls import path

from interattivo_worker import views

app_name = "interattivo_worker"

urlpatterns = [
    path(
        "pdf/pages/",
        views.PagesFromPdfWorkerView.as_view(),
        name="pages_from_pdf_worker",
    ),
]
