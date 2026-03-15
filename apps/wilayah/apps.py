import os
from django.apps import AppConfig


class WilayahConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'apps.wilayah'
    verbose_name       = 'Wilayah Indonesia'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(_auto_import_wilayah, sender=self)
        post_migrate.connect(_auto_import_bank,    sender=self)


# ─────────────────────────────────────────────────────────────────────────────
#  AUTO-IMPORT WILAYAH
# ─────────────────────────────────────────────────────────────────────────────

def _auto_import_wilayah(sender, **kwargs):
    """
    Auto-import data wilayah setelah migrate jika tabel masih kosong.
    File JSON dicari di: media/ → static/media/ → fixtures/
    """
    try:
        from apps.wilayah.models import Provinsi
        if Provinsi.objects.exists():
            return  # sudah ada, skip

        folder = _find_wilayah_folder()
        if not folder:
            print('[wilayah] File JSON wilayah tidak ditemukan — skip auto-import.')
            print('[wilayah] Taruh wilayah_provinsi.json, wilayah_kabupaten_kota.json,')
            print('[wilayah] wilayah_kecamatan.json, wilayah_desa_kelurahan.json di static/media/')
            return

        print('[wilayah] Data wilayah belum ada, mulai auto-import...')
        from django.core.management import call_command
        call_command('import_wilayah', folder=folder, verbosity=1)

        from apps.wilayah.models import Provinsi, Kabupaten, Kecamatan, Kelurahan
        print(
            f'[wilayah] ✓ Selesai — '
            f'{Provinsi.objects.count():,} provinsi, '
            f'{Kabupaten.objects.count():,} kabupaten, '
            f'{Kecamatan.objects.count():,} kecamatan, '
            f'{Kelurahan.objects.count():,} kelurahan.'
        )
    except Exception as e:
        print(f'[wilayah] Auto-import wilayah gagal: {e}')


def _find_wilayah_folder():
    """Cari folder yang berisi ke-4 file JSON wilayah."""
    try:
        from django.conf import settings
        candidates = [
            getattr(settings, 'MEDIA_ROOT', None),
            os.path.join(settings.BASE_DIR, 'media'),
            os.path.join(settings.BASE_DIR, 'static', 'media'),
            os.path.join(settings.BASE_DIR, 'fixtures'),
        ]
    except Exception:
        candidates = []

    required = [
        'wilayah_provinsi.json',
        'wilayah_kabupaten_kota.json',
        'wilayah_kecamatan.json',
        'wilayah_desa_kelurahan.json',
    ]
    for folder in candidates:
        if not folder or not os.path.isdir(folder):
            continue
        if all(os.path.exists(os.path.join(folder, f)) for f in required):
            return folder
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  AUTO-IMPORT BANK
# ─────────────────────────────────────────────────────────────────────────────

def _auto_import_bank(sender, **kwargs):
    """
    Auto-import data bank Indonesia setelah migrate jika tabel masih kosong.
    File bank_indonesia.json dicari di: media/ → static/media/ → fixtures/
    """
    try:
        from apps.wilayah.models import Bank
        if Bank.objects.exists():
            return  # sudah ada, skip

        json_path = _find_bank_json()
        if not json_path:
            print('[bank] File bank_indonesia.json tidak ditemukan — skip auto-import.')
            print('[bank] Taruh bank_indonesia.json di static/media/ atau fixtures/')
            return

        print(f'[bank] Data bank belum ada, import dari: {os.path.basename(json_path)}')
        from django.core.management import call_command
        call_command('import_bank', file=json_path, verbosity=1)

    except Exception as e:
        print(f'[bank] Auto-import bank gagal: {e}')


def _find_bank_json():
    """Cari bank_indonesia.json di media/ → static/media/ → fixtures/."""
    try:
        from django.conf import settings
        candidates = [
            getattr(settings, 'MEDIA_ROOT', None),
            os.path.join(settings.BASE_DIR, 'media'),
            os.path.join(settings.BASE_DIR, 'static', 'media'),
            os.path.join(settings.BASE_DIR, 'fixtures'),
        ]
    except Exception:
        candidates = []

    for folder in candidates:
        if not folder or not os.path.isdir(folder):
            continue
        path = os.path.join(folder, 'bank_indonesia.json')
        if os.path.exists(path):
            return path
    return None
