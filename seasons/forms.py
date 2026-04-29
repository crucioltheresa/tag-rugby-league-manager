from django import forms
from .models import Season, SeasonTimeSlot


class SeasonForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    class Meta:
        model = Season
        fields = [
            "name",
            "status",
            "venue",
            "start_date",
            "end_date",
            "num_rounds",
            "num_pitches",
        ]

    def clean(self):
        return super().clean()


class SeasonTimeSlotForm(forms.ModelForm):
    time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))

    class Meta:
        model = SeasonTimeSlot
        fields = ["time", "order"]
