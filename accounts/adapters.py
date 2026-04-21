from django.core.exceptions import ValidationError
from allauth.account.adapter import DefaultAccountAdapter
from core.models import EmailWhitelist


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        email = form.cleaned_data.get("email")

        if not EmailWhitelist.objects.filter(email=email, used=False).exists():
            raise ValidationError("Email is not authorized to register.")
        else:
            whitelist_entry = EmailWhitelist.objects.get(email=email, used=False)
            whitelist_entry.used = True
            whitelist_entry.save()
            if whitelist_entry.source == "admin":
                user.role = "captain"
            else:
                user.role = "player"
        return super().save_user(request, user, form, commit)
