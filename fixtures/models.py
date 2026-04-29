from django.db import models
from seasons.models import Season
from teams.models import Team


# Create your models here.
class Match(models.Model):
    id = models.AutoField(primary_key=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    team_a = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="team_a_matches"
    )
    team_b = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="team_b_matches"
    )
    round_number = models.IntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    pitch = models.CharField(max_length=50, blank=True)
    team_a_score = models.IntegerField(null=True, blank=True)
    team_b_score = models.IntegerField(null=True, blank=True)
    match_type = models.CharField(
        max_length=20,
        choices=[
            ("regular", "Regular"),
            ("semi_final", "Semi Final"),
            ("third_place", "Third Place"),
            ("final", "Final"),
        ],
        default="regular",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("scheduled", "Scheduled"),
            ("played", "Played"),
            ("cancelled", "Cancelled"),
        ],
        default="scheduled",
    )

    def __str__(self):
        return f"{self.team_a} vs {self.team_b} (Round {self.round_number}, {self.season})"
