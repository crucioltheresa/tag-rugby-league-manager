from django import forms
from .models import Match


class MatchForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}), required=False)

    class Meta:
        model = Match
        fields = ["date", "time"]


class ScheduleRoundForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))


class BulkScheduleForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Date of Round 1.",
    )
    interval_days = forms.IntegerField(
        initial=7,
        min_value=1,
        help_text="Days between each round.",
    )
    overwrite = forms.BooleanField(
        required=False,
        label="Overwrite already-scheduled rounds",
    )
