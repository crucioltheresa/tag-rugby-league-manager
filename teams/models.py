from django.db import models
from seasons.models import Season
from accounts.models import User


# Create your models here.
class Team(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    season = models.ForeignKey(
        Season,
        on_delete=models.CASCADE,
    )
    captain = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="captained_teams"
    )
    vice_captain = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="vc_teams", null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.season}"

    class Meta:
        unique_together = [("season", "captain")]


class Player(models.Model):
    id = models.AutoField(primary_key=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="user"
    )
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    registered = models.BooleanField(default=False)
