from django.db import models


# Create your models here.
class InterestResgistration(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
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


class EmailWhitelist(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    source = models.CharField(
        max_length=100, choices=[("admin", "Admin"), ("captain", "Captain")]
    )
    team = models.CharField(max_length=100, blank=True, null=True)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
