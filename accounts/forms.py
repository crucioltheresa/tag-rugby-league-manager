from django import forms
from django.contrib.auth import get_user_model
from allauth.account.forms import SignupForm

User = get_user_model()

GENDER_CHOICES = [
    ("male", "Male"),
    ("female", "Female"),
]


class CustomSignupForm(SignupForm):
    gender = forms.ChoiceField(choices=GENDER_CHOICES, label="Gender")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs["placeholder"] = "Confirm Password"

    def save(self, request):
        user = super().save(request)
        user.gender = self.cleaned_data["gender"]
        user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "profile_photo"]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email
