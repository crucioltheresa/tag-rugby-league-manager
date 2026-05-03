from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from core.models import EmailWhitelist, InterestRegistration
from fixtures.models import Match, PlayerAvailability
from seasons.models import Season
from teams.models import Team, Player


# Create your tests here.
class AccountsTests(TestCase):

    def test_user_creation(self):
        # Create a whitelist entry for testing
        EmailWhitelist.objects.create(source="admin", used=False, email="test@test.com")
        self.client.post(
            "/accounts/signup/",
            {
                "email": "test@test.com",
                "first_name": "Test",
                "last_name": "User",
                "username": "testuser",
                "password1": "testpassword",
                "password2": "testpassword",
            },
        )
        self.assertTrue(User.objects.filter(role="captain").exists())

    def test_admin_dashboard_non_staff_gets_403(self):
        user = User.objects.create_user(
            username="captain1", password="pass", role="captain"
        )
        self.client.force_login(user)
        response = self.client.get("/accounts/admin-dashboard/")
        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_staff_gets_200_with_context(self):
        user = User.objects.create_user(
            username="admin1", password="pass", role="admin"
        )
        InterestRegistration.objects.create(
            first_name="A", last_name="B", email="a@b.com", status="pending"
        )
        InterestRegistration.objects.create(
            first_name="C", last_name="D", email="c@d.com", status="approved"
        )
        self.client.force_login(user)
        response = self.client.get("/accounts/admin-dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["pending_interest_count"], 1)
        self.assertEqual(response.context["pending_team_count"], 0)
        self.assertEqual(response.context["active_season_name"], "No active season")

    def test_gender_saved_correctly_on_registration(self):
        EmailWhitelist.objects.create(source="captain", used=False, email="gendertest@test.com")
        self.client.post(
            "/accounts/signup/",
            {
                "email": "gendertest@test.com",
                "first_name": "Alex",
                "last_name": "Smith",
                "username": "alexsmith",
                "password1": "testpassword123",
                "password2": "testpassword123",
                "gender": "female",
            },
        )
        user = User.objects.get(email="gendertest@test.com")
        self.assertEqual(user.gender, "female")

    def test_player_email_gets_player_role_on_registration(self):
        # source="captain" means a captain added this player — adapter assigns role="player"
        EmailWhitelist.objects.create(source="captain", used=False, email="player@test.com")
        self.client.post(
            "/accounts/signup/",
            {
                "email": "player@test.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "username": "janedoe",
                "password1": "testpassword123",
                "password2": "testpassword123",
                "gender": "female",
            },
        )
        user = User.objects.filter(email="player@test.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, "player")

    def test_player_linked_to_correct_team_after_registration(self):
        captain = User.objects.create_user(
            username="capt", password="pass", role="captain", email="capt@test.com"
        )
        season = Season.objects.create(
            name="Spring 2025", status="active", venue="irishtown",
            start_date="2025-01-01", end_date="2025-06-30",
        )
        team = Team.objects.create(name="Eagles", season=season, captain=captain)
        Player.objects.create(
            team=team, email="newplayer@test.com", name="New Player", registered=False
        )
        EmailWhitelist.objects.create(source="captain", used=False, email="newplayer@test.com")
        self.client.post(
            "/accounts/signup/",
            {
                "email": "newplayer@test.com",
                "first_name": "New",
                "last_name": "Player",
                "username": "newplayer",
                "password1": "testpassword123",
                "password2": "testpassword123",
                "gender": "male",
            },
        )
        user = User.objects.filter(email="newplayer@test.com").first()
        self.assertIsNotNone(user)
        player = Player.objects.get(email="newplayer@test.com")
        self.assertEqual(player.user, user)
        self.assertTrue(player.registered)
        self.assertEqual(player.team, team)

    def test_unnapproved_email_block(self):
        self.client.post(
            "/accounts/signup/",
            {
                "email": "unapproved@test.com",
                "first_name": "Test",
                "last_name": "User",
                "username": "unapproveduser",
                "password1": "testpassword",
                "password2": "testpassword",
            },
            raise_request_exception=False,
        )
        self.assertFalse(User.objects.filter(role="captain").exists())


class ProfileManagementTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser", password="pass", role="player",
            email="profile@test.com", first_name="Jane", last_name="Doe", gender="female",
        )
        self.client.force_login(self.user)

    def test_valid_update_saves_correctly(self):
        self.client.post(reverse("profile"), {
            "first_name": "Janet",
            "last_name": "Smith",
            "email": "profile@test.com",
            "gender": "female",
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Janet")
        self.assertEqual(self.user.last_name, "Smith")

    def test_duplicate_email_shows_error(self):
        User.objects.create_user(
            username="other", password="pass", email="taken@test.com"
        )
        response = self.client.post(reverse("profile"), {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "taken@test.com",
            "gender": "female",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "email", "This email is already in use.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "profile@test.com")

    def test_fields_prepopulated_with_current_user_data(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.initial["first_name"], "Jane")
        self.assertEqual(form.initial["last_name"], "Doe")
        self.assertEqual(form.initial["email"], "profile@test.com")
        self.assertEqual(form.initial["gender"], "female")


class CaptainDashboardAvailabilityTests(TestCase):

    def setUp(self):
        self.captain = User.objects.create_user(
            username="captain", password="pass", role="captain",
            email="captain@test.com", gender="male",
        )
        opp_captain = User.objects.create_user(
            username="opp", password="pass", role="captain", email="opp@test.com"
        )
        self.season = Season.objects.create(
            name="Spring 2026", status="active", venue="irishtown",
            start_date="2026-01-01", end_date="2026-12-31",
        )
        self.team = Team.objects.create(name="Eagles", season=self.season, captain=self.captain)
        opponent = Team.objects.create(name="Hawks", season=self.season, captain=opp_captain)
        self.match = Match.objects.create(
            season=self.season, team_a=self.team, team_b=opponent,
            round_number=1, date=date.today() + timedelta(days=7), status="scheduled",
        )
        male_user = User.objects.create_user(
            username="mp1", password="pass", role="player", email="mp1@test.com", gender="male"
        )
        female_user = User.objects.create_user(
            username="fp1", password="pass", role="player", email="fp1@test.com", gender="female"
        )
        out_user = User.objects.create_user(
            username="out1", password="pass", role="player", email="out1@test.com", gender="female"
        )
        no_reply_user = User.objects.create_user(
            username="nr1", password="pass", role="player", email="nr1@test.com", gender="male"
        )
        male_player = Player.objects.create(team=self.team, user=male_user, email="mp1@test.com", name="Male One", registered=True)
        female_player = Player.objects.create(team=self.team, user=female_user, email="fp1@test.com", name="Female One", registered=True)
        out_player = Player.objects.create(team=self.team, user=out_user, email="out1@test.com", name="Out One", registered=True)
        Player.objects.create(team=self.team, user=no_reply_user, email="nr1@test.com", name="No Reply", registered=True)
        PlayerAvailability.objects.create(match=self.match, player=male_player, status="in")
        PlayerAvailability.objects.create(match=self.match, player=female_player, status="in")
        PlayerAvailability.objects.create(match=self.match, player=out_player, status="out")
        # no_reply_user has no PlayerAvailability record

    def test_availability_counts_calculated_correctly(self):
        self.client.force_login(self.captain)
        response = self.client.get(reverse("captain_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["in_count"], 2)
        self.assertEqual(response.context["out_count"], 1)
        self.assertEqual(response.context["no_reply_count"], 1)
        self.assertEqual(response.context["male_in"], 1)
        self.assertEqual(response.context["female_in"], 1)

    def test_availability_summary_shows_correct_mf_counts(self):
        # Add 2 extra males and 1 extra female, all "in"
        extras = [
            ("male", "m2", "m2@test.com", "Male Two"),
            ("male", "m3", "m3@test.com", "Male Three"),
            ("female", "f2", "f2@test.com", "Female Two"),
        ]
        for gender, username, email, name in extras:
            u = User.objects.create_user(
                username=username, password="pass", role="player", email=email, gender=gender,
            )
            p = Player.objects.create(team=self.team, user=u, email=email, name=name, registered=True)
            PlayerAvailability.objects.create(match=self.match, player=p, status="in")
        # setUp already has: 1 male "in", 1 female "in", 1 female "out", 1 male no reply
        # After extras: 3 males "in", 2 females "in"
        self.client.force_login(self.captain)
        response = self.client.get(reverse("captain_dashboard"))
        self.assertEqual(response.context["male_in"], 3)
        self.assertEqual(response.context["female_in"], 2)

    def test_non_captain_cannot_access_availability_summary(self):
        player = User.objects.create_user(
            username="plainplayer", password="pass", role="player", email="pp@test.com"
        )
        self.client.force_login(player)
        response = self.client.get(reverse("captain_dashboard"))
        self.assertEqual(response.status_code, 403)
