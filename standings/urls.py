from django.urls import path
from .views import standings_view

urlpatterns = [
    path("standings/<int:season_id>/", standings_view, name="standings"),
]
