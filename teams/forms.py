from django import forms
from .models import Team, User
from core.models import EmailWhitelist


class TeamRegistrationForm(forms.ModelForm):

    class Meta:
        model = Team
        fields = [
            "name",
            "vice_captain",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        whitelisted_emails = EmailWhitelist.objects.values_list("email", flat=True)
        self.fields["vice_captain"].queryset = User.objects.exclude(id=user.id).filter(
            email__in=whitelisted_emails
        )
