from django.urls import path
from .views import (
    generate_fixture_view,
    fixture_list,
    current_fixtures,
    schedule_round,
    delete_fixtures,
    my_fixtures,
    bulk_schedule,
    ics_match,
    match_edit,
    match_result,
    match_cancel,
)

urlpatterns = [
    path("fixtures/", current_fixtures, name="current_fixtures"),
    path("fixtures/my-team/", my_fixtures, name="my_fixtures"),
    path("fixtures/<int:season_id>/", fixture_list, name="fixture_list"),
    path(
        "fixtures/<int:season_id>/round/<int:round_number>/schedule/",
        schedule_round,
        name="schedule_round",
    ),
    path("fixtures/<int:match_id>/edit/", match_edit, name="edit_match"),
    path("fixtures/<int:match_id>/result/", match_result, name="result_match"),
    path("fixtures/<int:match_id>/cancel/", match_cancel, name="cancel_match"),
    path("fixtures/<int:fixture_id>/calendar/", ics_match, name="calendar_match"),
    path(
        "fixtures/generate/<int:season_id>/",
        generate_fixture_view,
        name="generate_fixtures",
    ),
    path("fixtures/delete/<int:season_id>/", delete_fixtures, name="delete_fixtures"),
    path(
        "fixtures/<int:season_id>/bulk-schedule/", bulk_schedule, name="bulk_schedule"
    ),
    # path(
    #     "fixtures/<id>/availability/",
    #     match_availability_summary,
    #     name="match_availability_summary",
    # ),
    # path(
    #     "fixtures/<id>/availability/confirm/",
    #     confirm_availability,
    #     name="confirm_availability",
    # ),
]
