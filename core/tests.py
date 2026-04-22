from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import InterestRegistration

User = get_user_model()

VALID_PAYLOAD = {
    "first_name": "User",
    "last_name": "Test",
    "email": "test@example.com",
    "phone_number": "",
    "team_name": "",
    "is_mixed": False,
    "estimated_players": "",
    "female_players": "",
    "male_players": "",
    "played_before": False,
    "message": "",
}


class HomepageViewTests(TestCase):

    def test_homepage_returns_200_and_uses_correct_template(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/index.html")


class InterestRegistrationViewTests(TestCase):

    def test_valid_submission_saves_with_pending_status(self):
        response = self.client.post(reverse("interest_registration"), VALID_PAYLOAD)

        self.assertRedirects(response, reverse("interest_success"))
        registration = InterestRegistration.objects.get(email="test@example.com")
        self.assertEqual(registration.status, "pending")

    def test_duplicate_email_shows_error(self):
        InterestRegistration.objects.create(
            first_name="Existing",
            last_name="User",
            email="test@example.com",
        )

        response = self.client.post(reverse("interest_registration"), VALID_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(InterestRegistration.objects.count(), 1)
        self.assertFormError(
            response.context["form"],
            "email",
            "Interest registration with this Email already exists.",
        )


class InterestListAccessTests(TestCase):

    def test_non_admin_cannot_access_interest_list(self):
        user = User.objects.create_user(username="player", password="pass")
        self.client.force_login(user)

        response = self.client.get(reverse("interest_list"))

        self.assertIn(response.status_code, [302, 403])
