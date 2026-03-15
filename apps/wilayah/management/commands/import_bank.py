"""
Management command: python manage.py import_bank
Import data bank Indonesia dari file JSON ke tabel Bank.

Cara pakai:
  python manage.py import_bank                           # cari bank_indonesia.json di media/
  python manage.py import_bank --file /path/bank.json   # file custom
  python manage.py import_bank --update                  # sync ulang (tambah baru, update existing)
  python manage.py import_bank --reset                   # hapus semua lalu import ulang

Alur update bank:
  1. Edit bank_indonesia.json di folder static/media/
  2. Jalankan: python manage.py import_bank --update
"""
import json
import os
from django.core.management.base import BaseCommand
from apps.wilayah.models import Bank


def _read_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


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


class Command(BaseCommand):
    help = 'Import data bank Indonesia dari JSON ke tabel Bank.'

    def add_arguments(self, parser):
        parser.add_argument('--file',   type=str, help='Path ke file JSON bank')
        parser.add_argument('--reset',  action='store_true', help='Hapus semua data bank sebelum import')
        parser.add_argument('--update', action='store_true', help='Sync dari JSON — tambah baru, update existing')

    def handle(self, *args, **options):
        if options['reset']:
            deleted, _ = Bank.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'{deleted} data bank dihapus.'))

        json_path = options.get('file') or _find_bank_json()

        if not json_path or not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(
                'File bank_indonesia.json tidak ditemukan.\n'
                'Taruh file di static/media/ atau gunakan --file.'
            ))
            return

        self.stdout.write(f'Membaca: {json_path}')
        rows = _read_json(json_path)
        if not rows:
            self.stdout.write(self.style.ERROR('File JSON kosong atau tidak bisa dibaca.'))
            return

        created = skipped = updated = 0
        for row in rows:
            kode  = row.get('kode', '').strip()
            nama  = row.get('nama', '').strip()
            alias = row.get('alias', '').strip()
            if not kode or not nama:
                continue

            if options['update']:
                obj, is_new = Bank.objects.update_or_create(
                    kode=kode, defaults={'nama': nama, 'alias': alias}
                )
                if is_new: created += 1
                else:      updated += 1
            else:
                _, is_new = Bank.objects.get_or_create(
                    kode=kode, defaults={'nama': nama, 'alias': alias}
                )
                if is_new: created += 1
                else:      skipped += 1

        mode = 'update' if options['update'] else 'import'
        self.stdout.write(self.style.SUCCESS(
            f'[{mode}] Selesai: {created} ditambahkan'
            + (f', {updated} diupdate' if options['update'] else f', {skipped} sudah ada')
            + f'. Total: {Bank.objects.count()} bank.'
        ))
