from datetime import date, timedelta

from django.db import models
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from seasons.models import Season, SeasonTimeSlot
from teams.models import Team, Player

from .models import Match, PlayerAvailability
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
            venue="irishtown",
            num_rounds=6,
            num_pitches=2,
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


class FixtureAccessTests(FixtureGenerationSetupMixin, TestCase):

    def test_unauthenticated_user_redirected_to_login(self):
        url = reverse("fixture_list", kwargs={"season_id": self.season.pk})
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('account_login')}?next={url}")

    def test_correct_fixtures_returned_for_active_season(self):
        generate_fixtures(self.season)
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("fixture_list", kwargs={"season_id": self.season.pk})
        )
        self.assertEqual(response.status_code, 200)
        rounds = response.context["rounds"]
        total_matches = sum(len(r["matches"]) for r in rounds)
        self.assertEqual(total_matches, Match.objects.filter(season=self.season).count())
        for r in rounds:
            for match in r["matches"]:
                self.assertEqual(match.season, self.season)


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


class MyFixturesTests(FixtureGenerationSetupMixin, TestCase):

    def setUp(self):
        super().setUp()
        generate_fixtures(self.season)
        self.team = self.teams[0]
        self.captain = self.team.captain
        self.vice_captain = self.team.vice_captain

    def test_vice_captain_sees_same_fixtures_as_captain(self):
        self.client.force_login(self.captain)
        captain_response = self.client.get(reverse("my_fixtures"))
        self.assertEqual(captain_response.status_code, 200)
        captain_ids = {m.id for m in captain_response.context["matches"]}

        self.client.force_login(self.vice_captain)
        vice_response = self.client.get(reverse("my_fixtures"))
        self.assertEqual(vice_response.status_code, 200)
        vice_ids = {m.id for m in vice_response.context["matches"]}

        self.assertEqual(captain_ids, vice_ids)
        self.assertGreater(len(captain_ids), 0)


class ICSTests(FixtureGenerationSetupMixin, TestCase):

    def setUp(self):
        super().setUp()
        generate_fixtures(self.season)
        self.match = Match.objects.filter(season=self.season).first()
        self.match.date = "2026-05-01"
        self.match.time = "18:00:00"
        self.match.save()

    def test_ics_returns_200_with_calendar_content_type(self):
        self.client.force_login(self.teams[0].captain)
        response = self.client.get(
            reverse("calendar_match", kwargs={"fixture_id": self.match.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/calendar", response["Content-Type"])


class MatchActionTests(FixtureGenerationSetupMixin, TestCase):

    def setUp(self):
        super().setUp()
        generate_fixtures(self.season)
        self.match = Match.objects.filter(season=self.season).first()
        self.captain = self.teams[0].captain

    # US-15: Edit match
    def test_valid_edit_saves_date_and_pitch(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse("edit_match", kwargs={"match_id": self.match.pk}),
            {"date": "2026-06-01", "time": "18:00", "pitch": "Pitch 2"},
        )
        self.match.refresh_from_db()
        self.assertEqual(str(self.match.date), "2026-06-01")
        self.assertEqual(self.match.pitch, "Pitch 2")

    def test_non_admin_edit_returns_403(self):
        self.client.force_login(self.captain)
        response = self.client.post(
            reverse("edit_match", kwargs={"match_id": self.match.pk}),
            {"date": "2026-06-01", "time": "18:00", "pitch": "Pitch 1"},
        )
        self.assertEqual(response.status_code, 403)

    # US-16: Record result
    def test_saving_result_sets_status_to_played(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse("result_match", kwargs={"match_id": self.match.pk}),
            {"team_a_score": 3, "team_b_score": 1},
        )
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, "played")
        self.assertEqual(self.match.team_a_score, 3)
        self.assertEqual(self.match.team_b_score, 1)

    def test_non_admin_result_returns_403(self):
        self.client.force_login(self.captain)
        response = self.client.post(
            reverse("result_match", kwargs={"match_id": self.match.pk}),
            {"team_a_score": 3, "team_b_score": 1},
        )
        self.assertEqual(response.status_code, 403)

    # US-17: Cancel match
    def test_cancel_sets_status_to_cancelled(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("cancel_match", kwargs={"match_id": self.match.pk}))
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, "cancelled")

    def test_non_admin_cancel_returns_403(self):
        self.client.force_login(self.captain)
        response = self.client.post(
            reverse("cancel_match", kwargs={"match_id": self.match.pk})
        )
        self.assertEqual(response.status_code, 403)


class PlayerAvailabilityTests(FixtureGenerationSetupMixin, TestCase):

    def setUp(self):
        super().setUp()
        generate_fixtures(self.season)
        self.team = self.teams[0]
        self.other_team = self.teams[1]
        self.player_user = User.objects.create_user(
            username="player1", email="player1@test.com", password="pass", role="player"
        )
        self.player = Player.objects.create(
            team=self.team,
            user=self.player_user,
            email="player1@test.com",
            name="Player One",
            registered=True,
        )
        # A match involving self.team
        self.team_match = Match.objects.filter(
            season=self.season
        ).filter(
            models.Q(team_a=self.team) | models.Q(team_b=self.team)
        ).first()
        self.team_match.date = date.today() + timedelta(days=7)
        self.team_match.save()
        # A match not involving self.team
        self.other_match = Match.objects.filter(
            season=self.season
        ).exclude(
            models.Q(team_a=self.team) | models.Q(team_b=self.team)
        ).first()
        self.other_match.date = date.today() + timedelta(days=7)
        self.other_match.save()

    def test_player_can_set_availability_for_own_team_match(self):
        self.client.force_login(self.player_user)
        self.client.post(
            reverse("set_availability", kwargs={"match_id": self.team_match.pk}),
            {"status": "in"},
        )
        avail = PlayerAvailability.objects.filter(
            match=self.team_match, player=self.player
        ).first()
        self.assertIsNotNone(avail)
        self.assertEqual(avail.status, "in")

    def test_player_cannot_set_availability_for_other_teams_match(self):
        self.client.force_login(self.player_user)
        self.client.post(
            reverse("set_availability", kwargs={"match_id": self.other_match.pk}),
            {"status": "in"},
        )
        self.assertFalse(
            PlayerAvailability.objects.filter(match=self.other_match, player=self.player).exists()
        )

    def test_availability_locked_after_match_date(self):
        self.team_match.date = date.today() - timedelta(days=1)
        self.team_match.save()
        self.client.force_login(self.player_user)
        self.client.post(
            reverse("set_availability", kwargs={"match_id": self.team_match.pk}),
            {"status": "in"},
        )
        self.assertFalse(
            PlayerAvailability.objects.filter(match=self.team_match, player=self.player).exists()
        )


class BulkScheduleTests(FixtureGenerationSetupMixin, TestCase):

    def setUp(self):
        super().setUp()
        generate_fixtures(self.season)
        # 1 time slot × 2 pitches = 2 slots, matching the 2 matches per round
        SeasonTimeSlot.objects.create(season=self.season, time="18:00", order=1)
        self.url = reverse("bulk_schedule", kwargs={"season_id": self.season.pk})
        self.client.force_login(self.admin)

    def test_all_unscheduled_rounds_get_date_time_pitch(self):
        self.client.post(self.url, {"start_date": "2026-03-01", "interval_days": 7})
        matches = list(Match.objects.filter(season=self.season).order_by("round_number", "id"))
        for match in matches:
            self.assertIsNotNone(match.date, msg=f"Round {match.round_number} match has no date")
            self.assertIsNotNone(match.time, msg=f"Round {match.round_number} match has no time")
            self.assertNotEqual(match.pitch, "", msg=f"Round {match.round_number} match has no pitch")
        # Round 1 → start_date, Round 2 → start_date + 7 days
        round1_dates = {str(m.date) for m in matches if m.round_number == 1}
        round2_dates = {str(m.date) for m in matches if m.round_number == 2}
        self.assertEqual(round1_dates, {"2026-03-01"})
        self.assertEqual(round2_dates, {"2026-03-08"})

    def test_already_scheduled_rounds_not_overwritten(self):
        Match.objects.filter(season=self.season, round_number=1).update(date="2025-12-01")
        self.client.post(self.url, {"start_date": "2026-03-01", "interval_days": 7})
        round1_dates = {
            str(m.date)
            for m in Match.objects.filter(season=self.season, round_number=1)
        }
        self.assertEqual(round1_dates, {"2025-12-01"})
        # Rounds 2–6 should have been assigned new dates
        unscheduled_after = Match.objects.filter(
            season=self.season, date=None
        ).exclude(round_number=1)
        self.assertEqual(unscheduled_after.count(), 0)
