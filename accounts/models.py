from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=[
            ("admin", "Admin"),
            ("captain", "Captain"),
            ("vice_captain", "Vice Captain"),
            ("player", "Player"),
        ],
        default="captain",
    )
