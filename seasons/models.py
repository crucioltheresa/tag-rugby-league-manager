from django.core.exceptions import ValidationError
from django.db import models

VENUE_CHOICES = [
    ("irishtown", "Irishtown Stadium, Dublin"),
    ("ballsbridge", "Pembroke Wanders, Dublin"),
    ("ucd", "UCD (Devlin GAA), Dublin"),
    ("sandymount", "Pembroke Cricket Club, Dublin"),
    ("clontarf", "Clontarf Road Astro Pitches, Dublin"),
    ("drumcondra", "Belvedere Rugby Grounds, Dublin"),
    ("grangegorman", "TUD Grangegorman, Dublin"),
]


# Create your models here.
class Season(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=100,
        choices=[("draft", "Draft"), ("active", "Active"), ("finished", "Finished")],
    )
    venue = models.CharField(max_length=200, blank=True, choices=VENUE_CHOICES)
    created_on = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date must be after start date.")

        if self.status == "active":
            qs = Season.objects.filter(status="active")
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Only one active season is allowed at a time.")
