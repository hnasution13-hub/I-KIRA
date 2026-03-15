#!/usr/bin/env python
"""
import_hierarki.py
==================
Import hierarki jabatan dari Excel hasil review ke database (update parent_id).

Cara pakai:
    python import_hierarki.py                              # pakai file default
    python import_hierarki.py --file /path/hierarki.xlsx  # file custom
    python import_hierarki.py --dry-run                    # preview tanpa simpan
    python import_hierarki.py --reset                      # reset semua parent_id ke NULL dulu
"""
import os, sys, django, argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hris_project.settings')
django.setup()

from apps.core.models import Position

def main(file_path, dry_run=False, reset=False):
    import openpyxl
    from collections import defaultdict

    mode = '[DRY RUN]' if dry_run else '[LIVE]'
    print(f'\n{mode} Import Hierarki Jabatan\n{"="*52}')

    if reset and not dry_run:
        n = Position.objects.all().update(parent=None)
        print(f'Reset: {n} jabatan parent_id → NULL\n')

    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb['Hierarki Jabatan']

    # Baca semua jabatan ke dalam cache nama → Position
    pos_by_nama = {}
    pos_by_id   = {}
    for p in Position.objects.select_related('department'):
        pos_by_nama[p.nama.lower().strip()] = p
        pos_by_id[p.id] = p

    updated = skipped = errors = 0

    for row in ws.iter_rows(min_row=4, values_only=True):
        if not row[0]: continue          # skip separator dept
        try:
            pos_id      = int(row[0])
        except (TypeError, ValueError):
            continue

        atasan_nama = str(row[4]).strip() if row[4] else ''

        pos = pos_by_id.get(pos_id)
        if not pos:
            print(f'  [SKIP] ID {pos_id} tidak ditemukan')
            skipped += 1
            continue

        if not atasan_nama:
            # Kosong = puncak hierarki
            if pos.parent_id is not None:
                print(f'  Root  : {pos.nama} → (puncak hierarki)')
                if not dry_run:
                    pos.parent = None
                    pos.save(update_fields=['parent'])
                updated += 1
            continue

        # Cari parent by nama
        parent = pos_by_nama.get(atasan_nama.lower())
        if not parent:
            # Fuzzy fallback
            from difflib import get_close_matches
            matches = get_close_matches(atasan_nama.lower(), pos_by_nama.keys(), n=1, cutoff=0.8)
            if matches:
                parent = pos_by_nama[matches[0]]
                print(f'  Fuzzy : "{atasan_nama}" → "{parent.nama}"')
            else:
                print(f'  [ERR] Atasan tidak ditemukan: "{atasan_nama}" untuk jabatan "{pos.nama}"')
                errors += 1
                continue

        # Cegah circular
        cur = parent
        is_circular = False
        while cur:
            if cur.id == pos_id:
                print(f'  [ERR] Circular: {pos.nama} tidak bisa jadi bawahan {parent.nama}')
                is_circular = True
                break
            cur = cur.parent
        if is_circular:
            errors += 1
            continue

        if pos.parent_id != parent.id:
            old_parent = pos.parent.nama if pos.parent else '(root)'
            print(f'  Update: {pos.nama:<35} → {parent.nama} (dari: {old_parent})')
            if not dry_run:
                pos.parent = parent
                pos.save(update_fields=['parent'])
            updated += 1
        else:
            skipped += 1

    print(f'\n{"="*52}')
    print(f'Updated : {updated}')
    print(f'Skipped : {skipped} (tidak berubah)')
    print(f'Error   : {errors}')
    if dry_run:
        print('\n[DRY RUN] Tidak ada yang disimpan. Jalankan tanpa --dry-run untuk apply.')
    else:
        print('\n✅ Selesai! Cek org chart untuk melihat hasilnya.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file',    default='hierarki_jabatan_review.xlsx')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--reset',   action='store_true', help='Reset semua parent_id ke NULL sebelum import')
    args = parser.parse_args()
    main(args.file, dry_run=args.dry_run, reset=args.reset)
