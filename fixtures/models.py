from django.db import models
from seasons.models import Season
from teams.models import Team


# Create your models here.
class Match(models.Model):
    id = models.AutoField(primary_key=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="home_matches")
