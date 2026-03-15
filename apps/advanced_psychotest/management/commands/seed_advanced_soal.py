"""
Management command: seed_advanced_soal
Seed bank soal untuk modul Advanced Psychometric Test.

Usage:
    python manage.py seed_advanced_soal             # seed jika belum ada
    python manage.py seed_advanced_soal --force     # hapus semua & seed ulang
    python manage.py seed_advanced_soal --aktifkan  # seed + aktifkan lisensi addon
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seed bank soal Advanced Psychometric Test ke database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Hapus semua soal yang ada lalu seed ulang dari awal',
        )
        parser.add_argument(
            '--aktifkan',
            action='store_true',
            help='Aktifkan lisensi addon advanced_psychotest setelah seed',
        )

    def handle(self, *args, **options):
        from apps.advanced_psychotest.seed_data import seed_all
        from apps.advanced_psychotest.models import AdvSoal

        force = options['force']
        aktifkan = options['aktifkan']

        jumlah_awal = AdvSoal.objects.count()

        if jumlah_awal > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'ℹ️  Sudah ada {jumlah_awal} soal di database. '
                    f'Gunakan --force untuk seed ulang.'
                )
            )
        else:
            if force and jumlah_awal > 0:
                self.stdout.write(f'🗑️  Menghapus {jumlah_awal} soal lama...')

            self.stdout.write('⏳ Seeding bank soal Advanced Psychometric Test...')
            seed_all(clear=force)

            jumlah_baru = AdvSoal.objects.count()
            self.stdout.write(self.style.SUCCESS(
                f'✅ Selesai — {jumlah_baru} soal berhasil di-seed'
            ))

            # Ringkasan per tipe
            from apps.advanced_psychotest.models import TEST_TYPE_CHOICES
            for ttype, tlabel in TEST_TYPE_CHOICES:
                n = AdvSoal.objects.filter(test_type=ttype, aktif=True).count()
                self.stdout.write(f'   {tlabel:<40} {n} soal')

        # Aktifkan lisensi addon jika diminta
        if aktifkan:
            pass  # Add-on diaktifkan via Django Admin
            if not created and not obj.aktif:
                obj.aktif = True
                obj.save(update_fields=['aktif'])
            self.stdout.write(self.style.SUCCESS(
                '✅ Lisensi addon advanced_psychotest diaktifkan'
            ))

        self.stdout.write('')
        self.stdout.write('Untuk menjalankan tes, pastikan:')
        self.stdout.write('  1. Soal sudah ter-seed  →  python manage.py seed_advanced_soal')
        self.stdout.write('  2. Lisensi aktif        →  python manage.py setup_addons --addon advanced_psychotest --aktifkan')
