from django.core.exceptions import ValidationError
from django.db import models


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
    created_on = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.start_date and self.end_date and self.start_date <= self.end_date:
            raise ValidationError({"End date mmust be after start date."})
