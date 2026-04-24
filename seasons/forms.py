from django import forms
from .models import Season


class SeasonForm(forms.ModelForm):
    class Meta:
        model = Season
        fields = [
            "name",
            "start_date",
            "end_date",
            "status",
        ]

    def clean(self):
        return super().clean()
