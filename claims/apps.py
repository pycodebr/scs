from django.apps import AppConfig


class ClaimsConfig(AppConfig):
    name = 'claims'

    def ready(self):
        import claims.signals  # noqa: F401
