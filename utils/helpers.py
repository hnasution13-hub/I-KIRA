"""
General utility functions

FIX BUG-009: format_rupiah() dan terbilang() dipindah ke number_utils.py
agar tidak ada duplikasi implementasi yang berbeda (helpers.py pakai koma,
number_utils.py pakai titik — format Indonesia yang benar).
Di sini hanya re-export agar kode lama yang import dari helpers.py tetap berjalan.
"""
# Re-export dari number_utils agar tidak ada duplikasi logika
from utils.number_utils import format_rupiah, terbilang  # noqa: F401
