"""
Management command: python manage.py reset_demo_accounts

Reset dan seed ulang data untuk semua akun Demo yang jadwalnya tiba.
Jalankan via cron:
  - Daily  : 0 0 * * *  python manage.py reset_demo_accounts
  - Atau paksa semua: python manage.py reset_demo_accounts --force-all

Logika:
  - Cek semua Company status='demo'
  - Jika demo_reset_schedule='daily'  → reset jika last_demo_reset > 1 hari lalu (atau belum pernah)
  - Jika demo_reset_schedule='weekly' → reset jika last_demo_reset > 7 hari lalu (atau belum pernah)
  - --force-all untuk paksa reset semua tanpa cek jadwal
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Reset dan seed ulang data akun Demo sesuai jadwal.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='Paksa reset semua company demo tanpa cek jadwal.',
        )
        parser.add_argument(
            '--company',
            type=str,
            help='Slug company tertentu yang ingin direset.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview tanpa benar-benar mereset.',
        )

    def handle(self, *args, **options):
        from apps.core.models import Company
        from apps.registration.demo_seed import full_reset_and_seed

        force_all  = options['force_all']
        dry_run    = options['dry_run']
        slug_filter = options.get('company')

        now = timezone.now()

        qs = Company.objects.filter(status='demo')
        if slug_filter:
            qs = qs.filter(slug=slug_filter)

        if not qs.exists():
            self.stdout.write(self.style.WARNING('Tidak ada company demo ditemukan.'))
            return

        reset_count = 0
        skip_count  = 0

        for company in qs:
            should_reset = force_all or self._should_reset(company, now)

            if not should_reset:
                self.stdout.write(f'  ⏭  {company.nama} — belum jadwalnya')
                skip_count += 1
                continue

            self.stdout.write(f'  🔄 {company.nama} [{company.demo_reset_schedule}]...')

            if not dry_run:
                try:
                    full_reset_and_seed(company)
                    self.stdout.write(self.style.SUCCESS(f'     ✅ Reset selesai'))
                    reset_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'     ❌ Error: {e}'))
            else:
                self.stdout.write(self.style.WARNING(f'     [DRY RUN] akan direset'))
                reset_count += 1

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN — {reset_count} akan direset, {skip_count} dilewati.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Selesai — {reset_count} direset, {skip_count} dilewati.'
            ))

    def _should_reset(self, company, now):
        """Cek apakah company ini perlu direset berdasarkan jadwal."""
        last = company.last_demo_reset
        if not last:
            return True  # Belum pernah direset

        if company.demo_reset_schedule == 'daily':
            return (now - last) >= timedelta(hours=23, minutes=50)  # toleransi 10 menit
        elif company.demo_reset_schedule == 'weekly':
            # Reset tiap Senin jam 00:00 — cek apakah sudah lewat Senin terakhir
            days_since = (now - last).days
            return days_since >= 7

        return False
