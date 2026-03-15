# Patch Ikira — Investor Dashboard + Paket & Limit Karyawan

## Struktur file patch ini:
```
apps/
├── core/
│   ├── models.py   → ganti file asli (tambah field paket, enforce_limit, addon_performance + properties)
│   └── admin.py    → ganti file asli (tambah kapasitas display, filter paket)
└── investor/       → copy seluruh folder ke apps/
    ├── __init__.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── admin.py
    ├── migrations/
    │   └── __init__.py
    └── templates/
        └── investor/
            ├── login.html
            ├── dashboard.html
            └── profil.html
```

## Langkah instalasi:
1. Copy semua file sesuai path di atas ke project
2. Tambah di hris_project/settings.py INSTALLED_APPS:
       'apps.investor',
3. Tambah di hris_project/urls.py:
       path('investor/', include('apps.investor.urls')),
4. Jalankan:
       python manage.py makemigrations core
       python manage.py makemigrations investor
       python manage.py migrate
5. Buat akun investor lewat shell:
       python manage.py shell
       from apps.investor.models import InvestorAccount
       acc = InvestorAccount(nama='Nama', username='investor1')
       acc.set_password('password')
       acc.save()
6. Buat InvestorPool lewat /admin/
7. Akses dashboard investor: /investor/
