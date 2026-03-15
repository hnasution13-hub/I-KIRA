from django.apps import AppConfig


class AdvancedPsychotestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.advanced_psychotest'
    verbose_name = 'Advanced Psychotest (Add-On)'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(_auto_seed_soal, sender=self)


def _auto_seed_soal(sender, **kwargs):
    """Auto-seed bank soal setelah migrate jika belum ada."""
    try:
        from apps.advanced_psychotest.models import AdvSoal
        from apps.advanced_psychotest.seed_data import seed_all
        if AdvSoal.objects.count() == 0:
            seed_all(clear=False)
    except Exception:
        pass
