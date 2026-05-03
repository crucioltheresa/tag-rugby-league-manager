from django.test import TestCase
from datetime import date
from accounts.models import User
from seasons.models import Season
from teams.models import Team
from fixtures.models import Match
from standings.models import Standing
from standings.utils import update_standings


def make_season():
    return Season.objects.create(
        name="Test Season",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 6, 1),
        status="active",
        venue="irishtown",
    )


def make_team(season, name, username):
    captain = User.objects.create_user(
        username=username, email=f"{username}@test.com", password="pass"
    )
    return Team.objects.create(name=name, season=season, captain=captain, status="approved")


def make_match(season, team_a, team_b, score_a, score_b):
    return Match.objects.create(
        season=season,
        team_a=team_a,
        team_b=team_b,
        team_a_score=score_a,
        team_b_score=score_b,
        status="played",
        round_number=1,
    )


class PointsCalculationTest(TestCase):
    """
    Uses 3 teams so Gamma absorbs the last-place penalty,
    leaving Alpha and Beta unaffected for the assertions.
    """

    def setUp(self):
        self.season = make_season()
        self.alpha = make_team(self.season, "Alpha", "alpha_cap")
        self.beta = make_team(self.season, "Beta", "beta_cap")
        self.gamma = make_team(self.season, "Gamma", "gamma_cap")

    def test_win_gives_4_points(self):
        # Alpha beats both opponents — clear winner, no penalty risk
        make_match(self.season, self.alpha, self.beta, 5, 2)
        make_match(self.season, self.alpha, self.gamma, 5, 2)
        make_match(self.season, self.beta, self.gamma, 3, 1)
        update_standings(self.season)

        # Alpha: 2 wins × 4 = 8pts
        standing = Standing.objects.get(season=self.season, team=self.alpha)
        self.assertEqual(standing.wins, 2)
        self.assertEqual(standing.points, 8)

    def test_loss_gives_0_points(self):
        # Beta loses to Alpha but beats Gamma, so Beta isn't last (Gamma absorbs penalty)
        make_match(self.season, self.alpha, self.beta, 5, 2)   # Beta loses
        make_match(self.season, self.alpha, self.gamma, 5, 2)  # Alpha wins
        make_match(self.season, self.beta, self.gamma, 3, 1)   # Beta wins
        update_standings(self.season)

        # Beta: 1W(4pts) + 1L(0pts) = 4pts
        standing = Standing.objects.get(season=self.season, team=self.beta)
        self.assertEqual(standing.losses, 1)
        self.assertEqual(standing.points, 4)

    def test_draw_gives_2_points(self):
        # Alpha draws Beta; Gamma loses both so it takes the last-place penalty
        make_match(self.season, self.alpha, self.beta, 3, 3)   # Draw
        make_match(self.season, self.alpha, self.gamma, 5, 1)  # Alpha wins
        make_match(self.season, self.beta, self.gamma, 5, 1)   # Beta wins
        update_standings(self.season)

        # Alpha: 1W(4pts) + 1D(2pts) = 6pts
        standing = Standing.objects.get(season=self.season, team=self.alpha)
        self.assertEqual(standing.draws, 1)
        self.assertEqual(standing.points, 6)


class StandingsSortingTest(TestCase):

    def setUp(self):
        self.season = make_season()
        self.alpha = make_team(self.season, "Alpha", "alpha_cap")
        self.beta = make_team(self.season, "Beta", "beta_cap")
        self.gamma = make_team(self.season, "Gamma", "gamma_cap")
        self.delta = make_team(self.season, "Delta", "delta_cap")

    def test_sorted_by_points_descending(self):
        # All teams get distinct points: Alpha 8, Beta 4, Gamma -2 (penalty), Delta 0 (no matches)
        make_match(self.season, self.alpha, self.beta, 5, 1)
        make_match(self.season, self.alpha, self.gamma, 5, 1)
        make_match(self.season, self.beta, self.gamma, 3, 1)
        update_standings(self.season)

        standings = list(Standing.objects.filter(season=self.season))
        self.assertEqual(standings[0].team, self.alpha)  # 8pts
        self.assertEqual(standings[1].team, self.beta)   # 4pts

    def test_tiebreak_by_wins(self):
        # Alpha: 1 win (4pts). Beta: 2 draws (4pts). Same points, different wins.
        # Delta absorbs the last-place penalty.
        make_match(self.season, self.alpha, self.delta, 5, 1)  # Alpha wins
        make_match(self.season, self.beta, self.gamma, 2, 2)   # Beta draws
        make_match(self.season, self.beta, self.delta, 2, 2)   # Beta draws
        update_standings(self.season)

        alpha_s = Standing.objects.get(season=self.season, team=self.alpha)
        beta_s = Standing.objects.get(season=self.season, team=self.beta)
        self.assertEqual(alpha_s.points, beta_s.points)  # both on 4pts

        standings = list(Standing.objects.filter(season=self.season))
        # Alpha has 1 win vs Beta's 0 wins — Alpha ranks higher
        self.assertEqual(standings[0].team, self.alpha)
        self.assertEqual(standings[1].team, self.beta)


class StandingsSignalTest(TestCase):

    def setUp(self):
        self.season = make_season()
        self.alpha = make_team(self.season, "Alpha", "alpha_cap")
        self.beta = make_team(self.season, "Beta", "beta_cap")

    def test_saving_played_match_triggers_standings_update(self):
        match = Match.objects.create(
            season=self.season,
            team_a=self.alpha,
            team_b=self.beta,
            round_number=1,
            status="scheduled",
        )
        self.assertFalse(Standing.objects.filter(season=self.season).exists())

        match.team_a_score = 4
        match.team_b_score = 1
        match.status = "played"
        match.save()

        standing = Standing.objects.get(season=self.season, team=self.alpha)
        self.assertEqual(standing.points, 4)

    def test_non_played_save_does_not_update_standings(self):
        match = Match.objects.create(
            season=self.season,
            team_a=self.alpha,
            team_b=self.beta,
            round_number=1,
            status="scheduled",
        )
        match.pitch = "Pitch 1"
        match.save()

        self.assertFalse(Standing.objects.filter(season=self.season).exists())


class LastPlacePenaltyTests(TestCase):

    def setUp(self):
        self.season = make_season()
        self.alpha = make_team(self.season, "Alpha", "alpha_cap")
        self.beta = make_team(self.season, "Beta", "beta_cap")
        self.gamma = make_team(self.season, "Gamma", "gamma_cap")

    def test_winless_last_place_receives_correct_penalty(self):
        make_match(self.season, self.alpha, self.beta, 3, 1)   # Alpha wins
        make_match(self.season, self.alpha, self.gamma, 3, 1)  # Alpha wins
        make_match(self.season, self.beta, self.gamma, 3, 1)   # Beta wins
        update_standings(self.season)
        # Gamma: 0 wins, 2 losses, 2 played → penalty = -played = -2
        gamma_s = Standing.objects.get(season=self.season, team=self.gamma)
        self.assertEqual(gamma_s.wins, 0)
        self.assertEqual(gamma_s.played, 2)
        self.assertEqual(gamma_s.points, -2)

    def test_last_place_team_with_win_is_not_penalised(self):
        # Circular results: every team ends on 1 win, 4 pts — last place has wins > 0
        make_match(self.season, self.alpha, self.beta, 3, 1)   # Alpha beats Beta
        make_match(self.season, self.beta, self.gamma, 3, 1)   # Beta beats Gamma
        make_match(self.season, self.gamma, self.alpha, 3, 1)  # Gamma beats Alpha
        update_standings(self.season)
        for team in [self.alpha, self.beta, self.gamma]:
            s = Standing.objects.get(season=self.season, team=team)
            self.assertEqual(s.wins, 1)
            self.assertEqual(s.points, 4)

    def test_penalty_recalculates_correctly_after_new_result(self):
        # Gamma loses twice → winless last place → penalty applied
        make_match(self.season, self.alpha, self.gamma, 3, 1)
        make_match(self.season, self.beta, self.gamma, 3, 1)
        gamma_s = Standing.objects.get(season=self.season, team=self.gamma)
        self.assertEqual(gamma_s.points, -2)

        # Gamma wins → signal re-runs update_standings → penalty removed
        make_match(self.season, self.gamma, self.beta, 3, 1)
        gamma_s.refresh_from_db()
        self.assertEqual(gamma_s.wins, 1)
        self.assertEqual(gamma_s.points, 4)  # 1 win × 4 pts, no penalty
