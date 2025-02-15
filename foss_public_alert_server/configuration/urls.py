from django.urls import path

from . import views

urlpatterns = [
    path("server_status", views.get_server_status, name="get_server_status"),
    path("", views.index)
]