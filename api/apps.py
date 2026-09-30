from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        from api.signals import (
            move_news2admin, move_news2report, move_profile2admin, create_user_profile
        )
