# ==================================================
# FILE: apps/custom_categories/utils.py
# PATH: D:/Project Pyton/Asset Management Django/apps/custom_categories/utils.py
# DESKRIPSI: Utility untuk generate nomor tag
# VERSION: 1.0.0
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from .models import CategoryCustom

def generate_next_tag(category_code):
    """
    Menghasilkan nomor tag berikutnya berdasarkan kode kategori.
    Format: {category_code}-XXXX (dengan 4 digit angka)
    """
    prefix = f"{category_code}-"
    # Cari tag terakhir dengan prefix yang sama
    last_tag = CategoryCustom.objects.filter(tag_number__startswith=prefix).order_by('tag_number').last()
    if last_tag:
        try:
            last_num = int(last_tag.tag_number.split('-')[-1])
            next_num = last_num + 1
        except:
            next_num = 1
    else:
        next_num = 1
    return f"{prefix}{next_num:04d}"