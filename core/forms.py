from .models import InterestRegistration
from django import forms


class InterestRegistrationForm(forms.ModelForm):
    class Meta:
        model = InterestRegistration
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "team_name",
            "is_mixed",
            "estimated_players",
            "female_players",
            "male_players",
            "played_before",
            "message",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound:
            for field_name, field in self.fields.items():
                if self.errors.get(field_name):
                    css = field.widget.attrs.get("class", "")
                    field.widget.attrs["class"] = f"{css} is-invalid".strip()

    def clean(self):
        cleaned_data = super().clean()
        is_mixed = cleaned_data.get("is_mixed")
        female = cleaned_data.get("female_players")
        male = cleaned_data.get("male_players")

        if is_mixed:
            if not female:
                self.add_error(
                    "female_players", "This field is required for mixed teams."
                )
            elif female < 3:
                self.add_error("female_players", "Insufficient female players.")

            if not male:
                self.add_error(
                    "male_players", "This field is required for mixed teams."
                )
            elif male < 4:
                self.add_error("male_players", "Insufficient male players.")
        return cleaned_data
