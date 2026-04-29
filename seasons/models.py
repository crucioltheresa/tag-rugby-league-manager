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
    venue = models.CharField(max_length=200, choices=VENUE_CHOICES)
    num_rounds = models.IntegerField(default=8)
    num_pitches = models.IntegerField(default=2)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.get_venue_display()} ({self.get_status_display()})"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date must be after start date.")

        if self.status == "active" and self.venue:
            qs = Season.objects.filter(status="active", venue=self.venue)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    f"There is already an active season at {self.get_venue_display()}."
                )


class SeasonTimeSlot(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="time_slots")
    time = models.TimeField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "time"]
        unique_together = [("season", "time")]

    def __str__(self):
        return f"{self.time.strftime('%H:%M')} ({self.season})"
