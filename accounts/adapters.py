from django.core.exceptions import ValidationError
from django.urls import reverse
from allauth.account.adapter import DefaultAccountAdapter
from core.models import EmailWhitelist


class CustomAccountAdapter(DefaultAccountAdapter):

    def save_user(self, request, user, form, commit=True):
        email = form.cleaned_data.get("email")
        try:
            whitelist_entry = EmailWhitelist.objects.get(email=email, used=False)
        except EmailWhitelist.DoesNotExist:
            raise ValidationError("Email is not authorized to register.")

        whitelist_entry.used = True
        whitelist_entry.save()
        user = super().save_user(request, user, form, commit)
        if whitelist_entry.source == "admin":
            user.role = "captain"
        else:
            user.role = "player"
        user.save()
        return user

    def clean_email(self, email):
        email = super().clean_email(email)
        if not EmailWhitelist.objects.filter(email=email, used=False).exists():
            raise ValidationError("Email is not authorized to register.")
        return email

    def get_login_redirect_url(self, request):
        if request.user.role == "admin":
            return reverse("admin_dashboard")
        elif request.user.role == "captain" or request.user.role == "vice_captain":
            return reverse("captain_dashboard")
        elif request.user.role == "player":
            return reverse("player_dashboard")
        return "/"
