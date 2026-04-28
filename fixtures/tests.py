from django.test import TestCase

from accounts.models import User
from seasons.models import Season
from teams.models import Team

from .models import Match
from .utils import generate_fixtures


class FixtureGenerationSetupMixin:
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin1", email="admin1@test.com", password="pass", role="admin"
        )
        self.season = Season.objects.create(
            name="Season 1",
            start_date="2026-01-01",
            end_date="2026-12-31",
            status="active",
        )
        self.teams = []
        for i in range(4):
            captain = User.objects.create_user(
                username=f"captain{i}",
                email=f"captain{i}@test.com",
                password="pass",
                role="captain",
            )
            vice = User.objects.create_user(
                username=f"vice{i}",
                email=f"vice{i}@test.com",
                password="pass",
                role="vice_captain",
            )
            team = Team.objects.create(
                name=f"Team {i + 1}",
                season=self.season,
                captain=captain,
                vice_captain=vice,
                status="approved",
            )
            self.teams.append(team)


class FixtureGenerationTests(FixtureGenerationSetupMixin, TestCase):

    def test_approved_teams_generate_matches(self):
        generate_fixtures(self.season)
        self.assertEqual(Match.objects.filter(season=self.season).count(), 12)

    def test_fewer_than_two_approved_teams_shows_error(self):
        for team in self.teams[1:]:
            team.status = "pending"
            team.save()

        with self.assertRaises(ValueError) as ctx:
            generate_fixtures(self.season)
        self.assertIn("At least 2 approved teams", str(ctx.exception))

    def test_cannot_generate_fixtures_twice_for_same_season(self):
        generate_fixtures(self.season)

        with self.assertRaises(ValueError) as ctx:
            generate_fixtures(self.season)
        self.assertIn("already been generated", str(ctx.exception))
