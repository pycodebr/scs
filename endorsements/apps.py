from django.apps import AppConfig


class EndorsementsConfig(AppConfig):
    name = 'endorsements'

    def ready(self):
        import endorsements.signals  # noqa: F401
