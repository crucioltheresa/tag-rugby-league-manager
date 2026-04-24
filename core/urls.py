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
    path("sign-up/", interest_registration_view, name="interest_registration"),
    path("sign-up/success/", interest_success_view, name="interest_success"),
    path("interests/", interest_list_view, name="interest_list"),
    path(
        "interests/<int:registration_id>/update_status/",
        update_submission_status_view,
        name="update_submission_status",
    ),
]
