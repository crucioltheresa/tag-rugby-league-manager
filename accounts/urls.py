from django.urls import path, include
from .views import admin_dashboard_view


urlpatterns = [
    path("", include("allauth.urls")),
    path(
        "admin-dashboard/",
        admin_dashboard_view,
        name="admin_dashboard",
    ),
]
