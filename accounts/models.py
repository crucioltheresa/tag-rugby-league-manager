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
    gender = models.CharField(
        max_length=20,
        choices=[
            ("male", "Male"),
            ("female", "Female"),
        ],
        blank=True,
    )
    profile_photo = models.ImageField(upload_to="profile_photos/", null=True, blank=True)
