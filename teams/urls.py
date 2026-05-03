from django.urls import path
from .views import (
    teams_list_view,
    team_create,
    update_team_status,
    team_edit,
    team_delete,
    squad_list,
    add_player,
    remove_player,
    set_vice_captain,
)

urlpatterns = [
    path("teams/", teams_list_view, name="teams_list_view"),
    path(
        "teams/<int:team_id>/update_status",
        update_team_status,
        name="update_team_status",
    ),
    path("teams/create", team_create, name="team_create"),
    path("teams/<int:team_id>/edit", team_edit, name="team_edit"),
    path("teams/<int:team_id>/delete", team_delete, name="team_delete"),
    path("teams/squad/", squad_list, name="squad_list"),
    path("teams/squad/add/", add_player, name="add_player"),
    path("teams/squad/<int:player_id>/remove/", remove_player, name="remove_player"),
    path("teams/squad/<int:player_id>/set-vc/", set_vice_captain, name="set_vice_captain"),
]
