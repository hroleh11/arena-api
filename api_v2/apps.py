from django.apps import AppConfig


class ApiV2Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_v2'

    def ready(self):
        import api_v2.signals  # noqa
