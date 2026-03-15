"""
Management command: setup_addons
Usage:
    python manage.py setup_addons              # seed semua addon (aktif=False)
    python manage.py setup_addons --aktifkan   # aktifkan semua addon
    python manage.py setup_addons --addon advanced_psychotest --aktifkan
"""
from django.core.management.base import BaseCommand
from apps.core.models import AddOnLicense


ADDONS = [
    ('assets',              'Asset Management'),
    ('recruitment',         'Rekrutmen'),
    ('psychotest',          'Psikotes'),
    ('advanced_psychotest', 'Advanced Psychometric Test'),
]


class Command(BaseCommand):
    help = 'Setup / seed record AddOnLicense ke database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--aktifkan',
            action='store_true',
            help='Aktifkan semua add-on (atau add-on tertentu jika --addon diisi)',
        )
        parser.add_argument(
            '--addon',
            type=str,
            help='Key add-on tertentu, misal: advanced_psychotest',
        )

    def handle(self, *args, **options):
        aktifkan = options['aktifkan']
        addon_filter = options.get('addon')

        targets = ADDONS
        if addon_filter:
            targets = [(k, l) for k, l in ADDONS if k == addon_filter]
            if not targets:
                self.stderr.write(self.style.ERROR(
                    f'Add-on "{addon_filter}" tidak dikenal. '
                    f'Pilihan: {", ".join(k for k, _ in ADDONS)}'
                ))
                return

        for addon_key, label in targets:
            obj, created = AddOnLicense.objects.get_or_create(
                addon=addon_key,
                defaults={'aktif': aktifkan}
            )
            if not created and aktifkan and not obj.aktif:
                obj.aktif = True
                obj.save(update_fields=['aktif'])
                self.stdout.write(self.style.SUCCESS(
                    f'✅ {label} — diaktifkan'
                ))
            elif created:
                status = 'aktif' if aktifkan else 'nonaktif'
                self.stdout.write(self.style.SUCCESS(
                    f'✅ {label} — record dibuat ({status})'
                ))
            else:
                status = 'aktif' if obj.aktif else 'nonaktif'
                self.stdout.write(
                    f'ℹ️  {label} — sudah ada ({status}), tidak diubah'
                )

        self.stdout.write('')
        self.stdout.write('Status saat ini:')
        for obj in AddOnLicense.objects.order_by('addon'):
            status = self.style.SUCCESS('✅ Aktif') if obj.aktif else self.style.WARNING('🔒 Nonaktif')
            self.stdout.write(f'   {obj.get_addon_display():<35} {status}')
