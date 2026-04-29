from django.urls import path, include
from .views import admin_dashboard_view, captain_dashboard_view, CustomLoginView, CustomSignupView, CustomLogoutView


urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="account_login"),
    path("signup/", CustomSignupView.as_view(), name="account_signup"),
    path("logout/", CustomLogoutView.as_view(), name="account_logout"),
    path("", include("allauth.urls")),
    path(
        "admin-dashboard/",
        admin_dashboard_view,
        name="admin_dashboard",
    ),
    path(
        "dashboard/",
        captain_dashboard_view,
        name="captain_dashboard",
    ),
]