from django.urls import path
from .views import (
    seasons_list_view,
    season_create,
    season_edit,
    season_delete,
    season_detail,
)

urlpatterns = [
    path("seasons/", seasons_list_view, name="seasons_list_view"),
    path("seasons/create/", season_create, name="season_create"),
    path("seasons/<int:season_id>/", season_detail, name="season_detail"),
    path("seasons/<int:season_id>/edit/", season_edit, name="season_edit"),
    path("seasons/<int:season_id>/delete/", season_delete, name="season_delete"),
]
