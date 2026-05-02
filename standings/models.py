from django.db import models
from seasons.models import Season
from teams.models import Team


# Create your models here.
class Standing(models.Model):
    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="standings"
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="standings")
    played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    byes = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = [("season", "team")]
        ordering = ["-points", "-wins"]

    def __str__(self):
        return f"{self.team.name} — {self.season.name}"
