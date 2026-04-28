from django.db import models
from seasons.models import Season
from teams.models import Team


# Create your models here.
class Match(models.Model):
    id = models.AutoField(primary_key=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    team_a = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_a")
    team_b = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_b")
    round_number = models.IntegerField(default=1)
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=200, null=True, blank=True)
    team_a_score = models.IntegerField(null=True, blank=True)
    team_b_score = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("scheduled", "Scheduled"),
            ("played", "Played"),
            ("cancelled", "Cancelled"),
        ],
        default="scheduled",
    )
