from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs["placeholder"] = "Confirm Password"
