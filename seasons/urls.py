from django.urls import path
from .views import (
    seasons_list_view,
    season_create,
    season_edit,
    season_delete,
    season_detail,
    add_time_slot,
    delete_time_slot,
)

urlpatterns = [
    path("seasons/", seasons_list_view, name="seasons_list_view"),
    path("seasons/create/", season_create, name="season_create"),
    path("seasons/<int:season_id>/", season_detail, name="season_detail"),
    path("seasons/<int:season_id>/edit/", season_edit, name="season_edit"),
    path("seasons/<int:season_id>/delete/", season_delete, name="season_delete"),
    path("seasons/<int:season_id>/timeslots/add/", add_time_slot, name="add_time_slot"),
    path("seasons/<int:season_id>/timeslots/<int:slot_id>/delete/", delete_time_slot, name="delete_time_slot"),
]
