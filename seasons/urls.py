from django.urls import path
from .views import (
    seasons_list_view,
    create_season,
    edit_season,
    delete_season,
    season_detail,
)

urlpatterns = [
    path("seasons/", seasons_list_view, name="seasons_list_view"),
    path("seasons/create/", create_season, name="create_season"),
    path("seasons/<int:season_id>/", season_detail, name="season_detail"),
    path("seasons/<int:season_id>/edit/", edit_season, name="season_edit"),
    path("seasons/<int:season_id>/delete/", delete_season, name="delete_season"),
]
