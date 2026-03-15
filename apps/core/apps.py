from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'apps.core'
    verbose_name       = 'Core'

    def ready(self):
        # Daftarkan signal handlers untuk audit log
        import apps.core.signals  # noqa: F401
