from django.urls import path
from .views import (
    teams_list_view,
    create_team,
    update_team_status,
    edit_team,
    delete_team,
)

urlpatterns = [
    path("teams/", teams_list_view, name="teams_list_view"),
    path(
        "teams/<int:team_id>/update_status",
        update_team_status,
        name="update_team_status",
    ),
    path("teams/create", create_team, name="create_team"),
    path("teams/<int:team_id>/edit", edit_team, name="edit_team"),
    path("teams/<int:team_id>/delete", delete_team, name="delete_team"),
]
