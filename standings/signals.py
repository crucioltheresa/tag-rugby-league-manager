from django.db.models.signals import post_save
from django.dispatch import receiver
from fixtures.models import Match
from .utils import update_standings


@receiver(post_save, sender=Match)
def on_match_saved(sender, instance, **kwargs):
    if instance.status == "played":
        update_standings(instance.season)
