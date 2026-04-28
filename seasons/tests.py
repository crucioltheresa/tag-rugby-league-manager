from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Season

User = get_user_model()


class SeasonFormValidationTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="pass", role="admin"
        )
        self.client.force_login(self.admin)

    def test_end_date_before_start_date_shows_error(self):
        response = self.client.post(reverse("create_season"), {
            "name": "Summer 2026",
            "start_date": "2026-09-01",
            "end_date": "2026-06-01",
            "status": "draft",
        })

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            None,
            "End date must be after start date.",
        )

    def test_two_active_seasons_raises_validation_error(self):
        Season.objects.create(
            name="Spring 2026",
            start_date="2026-03-01",
            end_date="2026-06-30",
            status="active",
            venue="Main Stadium",
        )

        response = self.client.post(reverse("create_season"), {
            "name": "Summer 2026",
            "start_date": "2026-07-01",
            "end_date": "2026-09-30",
            "status": "active",
        })

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            None,
            "Only one active season is allowed at a time.",
        )


class SeasonAccessTests(TestCase):

    def test_non_admin_cannot_access_season_management(self):
        captain = User.objects.create_user(
            username="captain1", password="pass", role="captain"
        )
        self.client.force_login(captain)

        response = self.client.get(reverse("seasons_list_view"))

        self.assertEqual(response.status_code, 403)
