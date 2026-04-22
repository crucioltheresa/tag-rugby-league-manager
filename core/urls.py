from django.urls import path
from .views import index_view, interest_registration_view, interest_success_view

urlpatterns = [
    path("", index_view, name="home"),
    path("interest/", interest_registration_view, name="interest_registration"),
    path("interest/success/", interest_success_view, name="interest_success"),
]
