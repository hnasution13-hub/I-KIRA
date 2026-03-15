# ==================================================
# FILE: apps/assets/depreciation.py
# PATH: D:/Project Pyton/Asset Management Django/apps/assets/depreciation.py
# DESKRIPSI: Fungsi untuk generate jadwal depresiasi aset
# PERBAIKAN: Validasi useful_life > 0, jika 0 lewati
# VERSION: 1.0.1
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from .models import Depreciation

def generate_depreciation(asset, commit=True):
    """
    Generate jadwal depresiasi untuk suatu asset.
    Jika useful_life <= 0, tidak ada depresiasi (kosongkan tabel).
    """
    # Hapus depresiasi lama
    Depreciation.objects.filter(asset=asset).delete()

    if asset.useful_life <= 0:
        return []  # tidak ada depresiasi

    purchase_price = float(asset.purchase_price)
    residual_value = float(asset.residual_value)
    useful_life = asset.useful_life

    monthly_dep = (purchase_price - residual_value) / (useful_life * 12)
    total_months = useful_life * 12

    year = asset.purchase_date.year
    month = asset.purchase_date.month

    accumulated = 0
    book_value = purchase_price

    dep_entries = []
    for i in range(total_months):
        accumulated += monthly_dep
        book_value -= monthly_dep
        if book_value < 0:
            book_value = 0

        dep_entries.append(Depreciation(
            asset=asset,
            year=year,
            month=month,
            monthly_depreciation=monthly_dep,
            accumulated_depreciation=accumulated,
            book_value=book_value
        ))

        month += 1
        if month > 12:
            month = 1
            year += 1

    if commit:
        if not asset.pk:
            raise ValueError(
                "bulk_create() prohibited to prevent data loss due to unsaved related object 'asset'. "
                "Save the asset first before generating depreciation."
            )
        Depreciation.objects.bulk_create(dep_entries)

    return dep_entries