from django.test import TestCase
from accounts.models import User
from core.models import EmailWhitelist, InterestRegistration


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
