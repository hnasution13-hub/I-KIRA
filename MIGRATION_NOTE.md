# MIGRATION NOTE — Clean Restart

## Status
Semua file migrasi `0*.py` telah dihapus (clean restart).
Folder `migrations/` dengan `__init__.py` tetap ada di setiap app.

## Sebelum Deploy

### 1. Reset Database Neon
Jalankan di Neon SQL Editor:
```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

### 2. Update build.sh
Tambahkan `makemigrations` sebelum `migrate`:
```bash
#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput --clear
python manage.py makemigrations --noinput
python manage.py migrate --noinput
```

### 3. Push ke GitHub → Render auto deploy

## Catatan Penting
- `makemigrations` di Render aman selama **model sudah final sebelum push**
- Jangan edit model setelah deploy tanpa push ulang
- Setelah deploy berhasil, buat superuser via Render Shell:
  ```
  python manage.py createsuperuser
  ```
