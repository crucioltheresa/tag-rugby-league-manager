from django.urls import path
from .views import generate_fixture_view

urlpatterns = [
    # path("/fixtures/", fixture_list, name="fixture_list"),
    # path("fixtures/my-team/", my_fixtures, name="my_fixtures"),
    # path("fixtures/<int:fixture_id>/edit/", edit_match, name="edit_match"),
    # path("fixtures/<int:fixture_id>/result/", result_match, name="result_match"),
    # path("fixtures/<int:fixture_id>/cancel/", cancel_match, name="cancel_match"),
    # path("fixtures/<int:fixture_id>/calendar/", ics_match, name="calendar_match"),
    path(
        "fixtures/generate/<int:season_id>/",
        generate_fixture_view,
        name="generate_fixtures",
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
