# Cara Integrasi Investor Dashboard ke Project Ikira

## 1. Copy folder app
Copy folder `apps/investor/` ke dalam project kamu di `apps/investor/`

## 2. Tambah ke INSTALLED_APPS
Di `hris_project/settings.py`, tambahkan:
```python
INSTALLED_APPS = [
    ...
    'apps.investor',
]
```

## 3. Tambah URL
Di `hris_project/urls.py`, tambahkan:
```python
path('investor/', include('apps.investor.urls')),
```

## 4. Migrate
```bash
python manage.py makemigrations investor
python manage.py migrate
```

## 5. Buat akun investor pertama
Lewat Django admin (`/admin/`) atau shell:
```python
from apps.investor.models import InvestorAccount
acc = InvestorAccount(nama='Nama Teman', username='investor1')
acc.set_password('passwordrahasia')
acc.save()
```

## 6. Isi milestone awal
Lewat Django admin, tambahkan milestone di model Milestone:
- "Platform selesai dibangun" → status: done
- "Deploy ke server berbayar" → status: ongoing
- "Client berbayar pertama" → status: planned
- "10 client aktif" → status: planned
- "Break even" → status: planned

## 7. Akses dashboard
URL investor: `/investor/`
URL login: `/investor/` (auto redirect)
URL dashboard: `/investor/home/`
URL API: `/investor/api/stats/` (hanya bisa diakses setelah login)

## Catatan Keamanan
- Investor TIDAK bisa akses `/admin/`
- Investor TIDAK bisa akses source code
- API hanya return angka yang kamu izinkan
- Session investor terpisah dari session user biasa
- Password di-hash dengan Django's make_password
