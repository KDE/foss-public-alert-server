from django.urls import path

from . import views

urlpatterns = [
    path("<uuid:identifier>", views.get_alert_cap_data),
    path("all", views.get_alerts_for_subscription_id, name="get_all_alerts"),
    path("debug", views.debug),
    path("", views.index)
]