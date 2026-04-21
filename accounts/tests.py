from django.test import TestCase
from accounts.models import User
from core.models import EmailWhitelist


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
