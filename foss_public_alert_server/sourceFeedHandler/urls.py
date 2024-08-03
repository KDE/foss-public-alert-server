from django.urls import path

from . import views

urlpatterns = [
    path("status", views.generate_source_status_page, name="status_page"),
    path("", views.index)
]