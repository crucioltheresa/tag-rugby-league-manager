from django.test import TestCase
from accounts.models import User
from core.models import EmailWhitelist
from seasons.models import Season
from .models import Team, Player


class TeamSetupMixin:
    def setUp(self):
        self.season = Season.objects.create(
            name="Season 1",
            start_date="2026-01-01",
            end_date="2026-12-31",
            status="active",
        )
        self.captain = User.objects.create_user(
            username="captain1", email="captain1@test.com", password="pass", role="captain"
        )
        self.vice_captain = User.objects.create_user(
            username="vicecaptain1", email="vc1@test.com", password="pass", role="vice_captain"
        )
        self.admin = User.objects.create_user(
            username="admin1", email="admin1@test.com", password="pass", role="admin"
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
            username="captain2", email="captain2@test.com", password="pass", role="captain"
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


# US-19: Squad Management
class SquadManagementTests(TeamSetupMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.team = Team.objects.create(
            name="Team A",
            season=self.season,
            captain=self.captain,
            vice_captain=self.vice_captain,
        )
        self.player_user = User.objects.create_user(
            username="player1", email="player1@test.com", password="pass", role="player"
        )

    # --- add_player ---

    def test_captain_can_add_player(self):
        self.client.force_login(self.captain)
        response = self.client.post(
            "/teams/squad/add/",
            {"name": "Alice Smith", "email": "alice@example.com"},
        )
        self.assertEqual(Player.objects.count(), 1)
        player = Player.objects.first()
        self.assertEqual(player.name, "Alice Smith")
        self.assertEqual(player.team, self.team)
        self.assertFalse(player.registered)

    def test_vice_captain_can_add_player(self):
        self.client.force_login(self.vice_captain)
        response = self.client.post(
            "/teams/squad/add/",
            {"name": "Bob Jones", "email": "bob@example.com"},
        )
        self.assertEqual(Player.objects.count(), 1)

    def test_add_player_creates_email_whitelist_entry(self):
        self.client.force_login(self.captain)
        self.client.post(
            "/teams/squad/add/",
            {"name": "Alice Smith", "email": "alice@example.com"},
        )
        self.assertTrue(EmailWhitelist.objects.filter(email="alice@example.com").exists())

    def test_duplicate_email_shows_error(self):
        Player.objects.create(team=self.team, name="Alice Smith", email="alice@example.com")
        self.client.force_login(self.captain)
        response = self.client.post(
            "/teams/squad/add/",
            {"name": "Alice Duplicate", "email": "alice@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Player.objects.count(), 1)
        messages = list(response.context["messages"])
        self.assertTrue(any("already in your squad" in str(m) for m in messages))

    def test_non_captain_cannot_access_add_player(self):
        self.client.force_login(self.player_user)
        response = self.client.get("/teams/squad/add/")
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_access_add_player(self):
        self.client.force_login(self.admin)
        response = self.client.get("/teams/squad/add/")
        self.assertEqual(response.status_code, 403)

    # --- squad_list ---

    def test_captain_can_view_squad_list(self):
        self.client.force_login(self.captain)
        response = self.client.get("/teams/squad/")
        self.assertEqual(response.status_code, 200)

    def test_non_captain_cannot_view_squad_list(self):
        self.client.force_login(self.player_user)
        response = self.client.get("/teams/squad/")
        self.assertEqual(response.status_code, 403)

    # --- remove_player ---

    def test_captain_can_remove_unregistered_player(self):
        player = Player.objects.create(team=self.team, name="Alice Smith", email="alice@example.com")
        EmailWhitelist.objects.create(email="alice@example.com")
        self.client.force_login(self.captain)
        self.client.post(f"/teams/squad/{player.id}/remove/")
        self.assertEqual(Player.objects.count(), 0)
        self.assertFalse(EmailWhitelist.objects.filter(email="alice@example.com").exists())

    def test_removing_registered_player_keeps_whitelist(self):
        player = Player.objects.create(
            team=self.team,
            name="Alice Smith",
            email="alice@example.com",
            user=self.player_user,
            registered=True,
        )
        EmailWhitelist.objects.create(email="alice@example.com")
        self.client.force_login(self.captain)
        self.client.post(f"/teams/squad/{player.id}/remove/")
        self.assertEqual(Player.objects.count(), 0)
        self.assertTrue(EmailWhitelist.objects.filter(email="alice@example.com").exists())

    def test_other_captain_cannot_remove_player(self):
        other_captain = User.objects.create_user(
            username="captain2", email="captain2b@test.com", password="pass", role="captain"
        )
        player = Player.objects.create(team=self.team, name="Alice Smith", email="alice@example.com")
        self.client.force_login(other_captain)
        response = self.client.post(f"/teams/squad/{player.id}/remove/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Player.objects.count(), 1)
