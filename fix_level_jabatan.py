"""
fix_level_jabatan.py
Script satu kali jalan untuk memperbaiki nilai level jabatan yang tidak valid di DB.

Cara pakai (Render Shell):
    python fix_level_jabatan.py

Mapping yang diperbaiki:
    'Director'      → 'Manajemen'        (kecuali Managing Director)
    'Senior Manager'→ 'Sr.Manager'
    'Senior Staff'  → 'Sr.Staff'         (jika ada yang salah input)
    'Senior Supervisor' → 'Sr.Supervisor'
"""

import os, sys, django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hris_project.settings')
django.setup()

from apps.core.models import Position

# Mapping: nama jabatan keyword → level yang benar
# Urutan penting: Managing Director harus dicek dulu sebelum Director
FIXES = [
    # (filter_level_salah, nama_contains, level_benar)
    ('Director', 'Managing',    'Corporate Manajemen'),
    ('Director', None,          'Manajemen'),
    ('Senior Manager', None,    'Sr.Manager'),
    ('Senior Staff', None,      'Sr.Staff'),
    ('Senior Supervisor', None, 'Sr.Supervisor'),
]

print('\n=== Fix Level Jabatan ===\n')
total = 0

for level_salah, nama_contains, level_benar in FIXES:
    qs = Position.objects.filter(level=level_salah)
    if nama_contains:
        qs = qs.filter(nama__icontains=nama_contains)
    count = qs.count()
    if count:
        qs.update(level=level_benar)
        print(f'  [OK] "{level_salah}"{f" (nama ~{nama_contains})" if nama_contains else ""}'
              f' → "{level_benar}" : {count} jabatan diupdate')
        total += count
    else:
        print(f'  [-] "{level_salah}"{f" (nama ~{nama_contains})" if nama_contains else ""}'
              f' → tidak ada data, skip.')

print(f'\nTotal: {total} jabatan diperbaiki.')

# Verifikasi — tampilkan level yang masih tidak valid
from apps.core.models import Position
VALID_LEVELS = {v for v, _ in Position.LEVEL_CHOICES}
invalid = Position.objects.exclude(level__in=VALID_LEVELS)
if invalid.exists():
    print(f'\n[!] Masih ada {invalid.count()} jabatan dengan level tidak valid:')
    for p in invalid[:10]:
        print(f'    - {p.nama} | level="{p.level}" | company={p.company}')
else:
    print('\n[OK] Semua level jabatan sudah valid.')

# ── Hapus duplikat jabatan per company ────────────────────────────────────────
print('\n=== Hapus Duplikat Jabatan ===\n')
from apps.core.models import Company
from django.db.models import Min

total_del = 0
for company in Company.objects.all():
    positions = Position.objects.filter(company=company)
    # Group by nama — simpan ID terkecil (pertama dibuat), hapus sisanya
    seen = {}
    to_delete = []
    for pos in positions.order_by('id'):
        key = pos.nama.strip().lower()
        if key in seen:
            to_delete.append(pos.pk)
        else:
            seen[key] = pos.pk

    if to_delete:
        Position.objects.filter(pk__in=to_delete).delete()
        print(f'  [OK] {company.nama}: {len(to_delete)} duplikat dihapus.')
        total_del += len(to_delete)
    else:
        print(f'  [-] {company.nama}: tidak ada duplikat.')

print(f'\nTotal duplikat dihapus: {total_del}')
