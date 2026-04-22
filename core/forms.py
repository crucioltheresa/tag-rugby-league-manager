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
