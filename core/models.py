from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# Create your models here.
class InterestRegistration(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    team_name = models.CharField(max_length=100, blank=True, null=True)
    is_mixed = models.BooleanField(default=False)
    estimated_players = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(7), MaxValueValidator(14)],
    )
    female_players = models.PositiveIntegerField(
        blank=True, null=True, validators=[MinValueValidator(3)]
    )
    male_players = models.PositiveIntegerField(
        blank=True, null=True, validators=[MinValueValidator(4)]
    )
    played_before = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class EmailWhitelist(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    source = models.CharField(
        max_length=100, choices=[("admin", "Admin"), ("captain", "Captain")]
    )
    interest_registration = models.ForeignKey(
        InterestRegistration, null=True, blank=True, on_delete=models.SET_NULL
    )
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
