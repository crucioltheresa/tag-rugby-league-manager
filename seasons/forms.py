from django import forms
from django.core.exceptions import ValidationError
from .models import Season


class SeasonForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

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
