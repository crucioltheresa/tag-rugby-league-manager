from django.apps import AppConfig


class StandingsConfig(AppConfig):
    name = "standings"

    def ready(self):
        import standings.signals
