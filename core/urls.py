from django.urls import path
from .views import (
    IndexView,
    interest_registration_view,
    interest_success_view,
    update_submission_status_view,
    interest_list_view,
)

urlpatterns = [
    path("", IndexView, name="home"),
    path("join/", interest_registration_view, name="interest_registration"),
    path("join/success/", interest_success_view, name="interest_success"),
    path("join/admin/list/", interest_list_view, name="interest_list"),
    path(
        "join/admin/<int:registration_id>/status/",
        update_submission_status_view,
        name="update_submission_status",
    ),
]
