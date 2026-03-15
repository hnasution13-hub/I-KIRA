"""
Management command: expire_adv_sessions

Tandai sesi advanced test yang sudah lewat batas waktu sebagai 'expired'.
Jalankan via cron / Celery beat, contoh:
    0 * * * * python manage.py expire_adv_sessions   # setiap jam

Usage:
    python manage.py expire_adv_sessions
    python manage.py expire_adv_sessions --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Tandai sesi Advanced Test yang sudah kadaluarsa sebagai expired'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Tampilkan sesi yang akan di-expire tanpa mengubah database',
        )

    def handle(self, *args, **options):
        from apps.advanced_psychotest.models import AdvSession

        now = timezone.now()
        dry_run = options['dry_run']

        qs = AdvSession.objects.filter(
            status__in=['pending', 'started'],
            expired_at__lt=now,
        )

        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('✅ Tidak ada sesi yang perlu di-expire.'))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY-RUN] {count} sesi akan di-expire:')
            )
            for s in qs.select_related('candidate', 'employee'):
                peserta = s.get_peserta_nama()
                self.stdout.write(
                    f'  • #{s.pk} | {peserta} | expired_at: {s.expired_at:%d/%m/%Y %H:%M}'
                )
        else:
            updated = qs.update(status='expired')
            self.stdout.write(self.style.SUCCESS(
                f'✅ {updated} sesi berhasil ditandai sebagai expired.'
            ))
