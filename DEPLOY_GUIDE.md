# Panduan Deploy Ikira HRIS ke Render.com

## Yang sudah disiapkan otomatis:
- render.yaml — konfigurasi deploy
- build.sh — script build otomatis
- whitenoise — untuk serve static files
- dj-database-url — koneksi PostgreSQL otomatis
- /ping/ endpoint — untuk anti-sleep

---

## LANGKAH 1 — Push ke GitHub

```bash
git init
git add .
git commit -m "Initial deploy Ikira HRIS"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

> Pastikan db.sqlite3 ada di .gitignore (sudah ada)

---

## LANGKAH 2 — Deploy ke Render

1. Buka https://render.com → Sign up/login pakai GitHub
2. Klik **"New +"** → **"Blueprint"**
3. Connect ke repo GitHub kamu
4. Render akan baca `render.yaml` otomatis
5. Klik **"Apply"** → tunggu build selesai (5-10 menit)

Setelah selesai, app akan jalan di:
`https://ikira-hris.onrender.com`

---

## LANGKAH 3 — Buat akun investor pertama

Setelah deploy, buka Render dashboard → **Shell** tab, lalu:

```bash
python manage.py shell
```

```python
from apps.investor.models import InvestorAccount, InvestorPool

# Buat pool investasi
pool = InvestorPool()
pool.nama = 'Pool Investasi Ikira'
pool.total_dana = 4000000
pool.modal_founder = 2000000
pool.save()

# Buat akun investor kamu
acc = InvestorAccount()
acc.pool = pool
acc.nama = 'Founder'
acc.username = 'founder'
acc.aktif = True
acc.set_password('passwordkamu')
acc.save()
print("Done!")
```

---

## LANGKAH 4 — Setup Anti-Sleep di cron-job.org

Render free tier auto-sleep setelah 15 menit tidak ada request.
Kita ping setiap 10 menit dari jam 04.00-23.00 WIB.

1. Buka https://cron-job.org → daftar gratis
2. Klik **"CREATE CRONJOB"**
3. Isi:
   - **Title**: Ikira Keepalive
   - **URL**: `https://ikira-hris.onrender.com/ping/`
   - **Schedule**: Every 10 minutes
4. Klik tab **"Advanced"** → **"Execution times"**
5. Set jam aktif: **21:00 - 16:00 UTC** (= 04:00 - 23:00 WIB, karena UTC+7)
6. Save

Sekarang server akan tetap aktif jam 04.00-23.00 WIB, dan tidur jam 23.00-04.00 WIB.

---

## LANGKAH 5 — Environment Variables (kalau perlu tambah)

Di Render dashboard → service ikira-hris → **Environment**:

| Key | Value |
|-----|-------|
| SECRET_KEY | (auto generated) |
| DEBUG | False |
| ALLOWED_HOSTS | ikira-hris.onrender.com |
| SITE_URL | https://ikira-hris.onrender.com |
| SALES_WA | 628XXXXXXXXXX |
| SALES_EMAIL | sales@ikira.id |
| EMAIL_HOST | smtp.gmail.com |
| EMAIL_PORT | 587 |
| EMAIL_HOST_USER | emailkamu@gmail.com |
| EMAIL_HOST_PASSWORD | app-password-gmail |
| DEFAULT_FROM_EMAIL | Ikira HRIS <emailkamu@gmail.com> |

---

## URL Penting Setelah Deploy:

| URL | Fungsi |
|-----|--------|
| `/` | Landing / Login |
| `/login/` | Login HR |
| `/admin/` | Admin panel |
| `/daftar/` | Registrasi demo/trial |
| `/investor/` | Dashboard investor |
| `/ping/` | Health check (untuk cron) |

---

## Tips:
- Database PostgreSQL gratis di Render bertahan 90 hari
- Setelah 90 hari, export data dulu lalu buat database baru
- Atau upgrade ke paket berbayar kalau sudah ada revenue
