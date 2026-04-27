from django.test import TestCase
from accounts.models import User
from seasons.models import Season
from .models import Team


class TeamSetupMixin:
    def setUp(self):
        self.season = Season.objects.create(
            name="Season 1",
            start_date="2026-01-01",
            end_date="2026-12-31",
            status="active",
        )
        self.captain = User.objects.create_user(
            username="captain1", password="pass", role="captain"
        )
        self.vice_captain = User.objects.create_user(
            username="vicecaptain1", password="pass", role="vice_captain"
        )
        self.admin = User.objects.create_user(
            username="admin1", password="pass", role="admin"
        )


# US-08: Team Registration
class TeamRegistrationTests(TeamSetupMixin, TestCase):

    def test_captain_can_register_team(self):
        self.client.force_login(self.captain)
        response = self.client.post(
            "/teams/create",
            {"name": "Team A", "vice_captain": self.vice_captain.id},
        )
        self.assertEqual(Team.objects.count(), 1)
        team = Team.objects.first()
        self.assertEqual(team.captain, self.captain)
        self.assertEqual(team.season, self.season)
        self.assertEqual(team.status, "pending")

    def test_captain_cannot_register_twice_in_same_season(self):
        Team.objects.create(
            name="Team A",
            season=self.season,
            captain=self.captain,
            vice_captain=self.vice_captain,
        )
        self.client.force_login(self.captain)
        response = self.client.post(
            "/teams/create",
            {"name": "Team B", "vice_captain": self.vice_captain.id},
        )
        self.assertEqual(Team.objects.count(), 1)

    def test_captain_and_vice_captain_cannot_be_same_user(self):
        self.client.force_login(self.captain)
        response = self.client.post(
            "/teams/create",
            {"name": "Team A", "vice_captain": self.captain.id},
        )
        self.assertEqual(Team.objects.count(), 0)

    def test_non_captain_cannot_register_team(self):
        self.client.force_login(self.admin)
        response = self.client.get("/teams/create")
        self.assertEqual(response.status_code, 403)


# US-09: Team Approval
class TeamApprovalTests(TeamSetupMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.team = Team.objects.create(
            name="Team A",
            season=self.season,
            captain=self.captain,
            vice_captain=self.vice_captain,
        )

    def test_admin_can_approve_team(self):
        self.client.force_login(self.admin)
        self.client.post(
            f"/teams/{self.team.id}/update_status",
            {"status": "approved"},
        )
        self.team.refresh_from_db()
        self.assertEqual(self.team.status, "approved")

    def test_admin_can_reject_team(self):
        self.client.force_login(self.admin)
        self.client.post(
            f"/teams/{self.team.id}/update_status",
            {"status": "rejected"},
        )
        self.team.refresh_from_db()
        self.assertEqual(self.team.status, "rejected")

    def test_non_admin_cannot_access_teams_list(self):
        self.client.force_login(self.captain)
        response = self.client.get("/teams/")
        self.assertEqual(response.status_code, 403)

    def test_non_admin_cannot_update_team_status(self):
        self.client.force_login(self.captain)
        response = self.client.post(
            f"/teams/{self.team.id}/update_status",
            {"status": "approved"},
        )
        self.assertEqual(response.status_code, 403)
        self.team.refresh_from_db()
        self.assertEqual(self.team.status, "pending")


# US-10: Team Editing
class TeamEditTests(TeamSetupMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.team = Team.objects.create(
            name="Team A",
            season=self.season,
            captain=self.captain,
            vice_captain=self.vice_captain,
        )

    def test_captain_can_edit_own_team(self):
        self.client.force_login(self.captain)
        response = self.client.post(
            f"/teams/{self.team.id}/edit",
            {"name": "Team A Updated", "vice_captain": self.vice_captain.id},
        )
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, "Team A Updated")

    def test_vice_captain_can_edit_own_team(self):
        self.client.force_login(self.vice_captain)
        response = self.client.post(
            f"/teams/{self.team.id}/edit",
            {"name": "Team A Updated", "vice_captain": self.vice_captain.id},
        )
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, "Team A Updated")

    def test_other_captain_cannot_edit_team(self):
        other_captain = User.objects.create_user(
            username="captain2", password="pass", role="captain"
        )
        self.client.force_login(other_captain)
        response = self.client.post(
            f"/teams/{self.team.id}/edit",
            {"name": "Hacked Name", "vice_captain": self.vice_captain.id},
        )
        self.assertEqual(response.status_code, 403)
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, "Team A")

    # TODO: test that edit is disabled after fixture generation (US-10)
