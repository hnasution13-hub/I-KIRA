"""
Management command untuk import data wilayah Indonesia dari JSON.

File JSON yang dibutuhkan (ada di static/media/):
  wilayah_provinsi.json        : [{kode, nama}]
  wilayah_kabupaten_kota.json  : [{kode, nama, kode_provinsi}]
  wilayah_kecamatan.json       : [{kode, nama, kode_kabkota, kode_provinsi}]
  wilayah_desa_kelurahan.json  : [{kode, nama, kode_kecamatan, kode_kabkota, kode_provinsi, kode_pos}]

Cara pakai:
  python manage.py import_wilayah
  python manage.py import_wilayah --folder /path/to/json/folder
  python manage.py import_wilayah --reset
"""
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.wilayah.models import Provinsi, Kabupaten, Kecamatan, Kelurahan


def _read_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


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


class Command(BaseCommand):
    help = 'Import data wilayah Indonesia dari file JSON'

    def add_arguments(self, parser):
        parser.add_argument('--folder', type=str, help='Path ke folder berisi file JSON wilayah')
        parser.add_argument('--reset',  action='store_true', help='Hapus semua data wilayah sebelum import')

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Menghapus data wilayah lama...')
            Kelurahan.objects.all().delete()
            Kecamatan.objects.all().delete()
            Kabupaten.objects.all().delete()
            Provinsi.objects.all().delete()
            self.stdout.write(self.style.WARNING('Data wilayah dihapus.'))

        folder = options.get('folder') or _find_wilayah_folder()
        if not folder:
            self.stdout.write(self.style.ERROR(
                'Folder JSON wilayah tidak ditemukan.\n'
                'Pastikan wilayah_provinsi.json, wilayah_kabupaten_kota.json,\n'
                'wilayah_kecamatan.json, wilayah_desa_kelurahan.json\n'
                'ada di static/media/ atau gunakan --folder.'
            ))
            return

        self._import_from_folder(folder)

    @transaction.atomic
    def _import_from_folder(self, folder):
        files = {
            'provinsi':  os.path.join(folder, 'wilayah_provinsi.json'),
            'kabupaten': os.path.join(folder, 'wilayah_kabupaten_kota.json'),
            'kecamatan': os.path.join(folder, 'wilayah_kecamatan.json'),
            'kelurahan': os.path.join(folder, 'wilayah_desa_kelurahan.json'),
        }
        for label, path in files.items():
            if not os.path.exists(path):
                self.stdout.write(self.style.ERROR(f'File tidak ditemukan: {os.path.basename(path)}'))
                return

        self.stdout.write(f'Membaca JSON dari: {folder}\n')

        # ── 1. PROVINSI ──────────────────────────────────────────────────────
        self.stdout.write('Import provinsi...')
        count = 0
        for row in (_read_json(files['provinsi']) or []):
            kode = row.get('kode', '').strip()
            nama = row.get('nama', '').strip()
            if kode and nama:
                Provinsi.objects.get_or_create(kode=kode, defaults={'nama': nama})
                count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} provinsi'))

        # ── 2. KABUPATEN/KOTA ────────────────────────────────────────────────
        self.stdout.write('Import kabupaten/kota...')
        prov_map = {p.kode: p for p in Provinsi.objects.all()}
        count = 0
        for row in (_read_json(files['kabupaten']) or []):
            kode      = row.get('kode', '').strip()
            nama      = row.get('nama', '').strip()
            kode_prov = row.get('kode_provinsi', '').strip()
            prov      = prov_map.get(kode_prov)
            if kode and nama and prov:
                Kabupaten.objects.get_or_create(kode=kode, defaults={'nama': nama, 'provinsi': prov})
                count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} kabupaten/kota'))

        # ── 3. KECAMATAN ─────────────────────────────────────────────────────
        self.stdout.write('Import kecamatan...')
        kab_map = {k.kode: k for k in Kabupaten.objects.all()}
        count = 0
        for row in (_read_json(files['kecamatan']) or []):
            kode     = row.get('kode', '').strip()
            nama     = row.get('nama', '').strip()
            kode_kab = row.get('kode_kabkota', '').strip()
            kab      = kab_map.get(kode_kab)
            if kode and nama and kab:
                Kecamatan.objects.get_or_create(kode=kode, defaults={'nama': nama, 'kabupaten': kab})
                count += 1
        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} kecamatan'))

        # ── 4. KELURAHAN/DESA ────────────────────────────────────────────────
        self.stdout.write('Import kelurahan/desa...')
        kec_map = {k.kode: k for k in Kecamatan.objects.all()}
        rows    = _read_json(files['kelurahan']) or []
        total   = len(rows)
        step    = max(total // 20, 1)
        count   = 0
        for i, row in enumerate(rows):
            if i % step == 0:
                self.stdout.write(f'  {int(i/total*100)}% ({i:,}/{total:,})', ending='\r')
                self.stdout.flush()
            kode     = row.get('kode', '').strip()
            nama     = row.get('nama', '').strip()
            kode_kec = row.get('kode_kecamatan', '').strip()
            kode_pos = row.get('kode_pos', '').strip()
            kec      = kec_map.get(kode_kec)
            if kode and nama and kec:
                Kelurahan.objects.get_or_create(
                    kode=kode,
                    defaults={'nama': nama, 'kecamatan': kec, 'kode_pos': kode_pos}
                )
                count += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'  ✓ {count} kelurahan/desa'))

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Import selesai!\n'
            f'   Provinsi  : {Provinsi.objects.count():,}\n'
            f'   Kabupaten : {Kabupaten.objects.count():,}\n'
            f'   Kecamatan : {Kecamatan.objects.count():,}\n'
            f'   Kelurahan : {Kelurahan.objects.count():,}'
        ))
