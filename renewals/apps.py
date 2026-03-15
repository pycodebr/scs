from django.apps import AppConfig


class RenewalsConfig(AppConfig):
    name = 'renewals'

    def ready(self):
        import renewals.signals  # noqa: F401
