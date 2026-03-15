"""
Date utility functions untuk HRIS SmartDesk
"""
from datetime import date, datetime, timedelta
import calendar


def hitung_masa_kerja(join_date, end_date=None):
    """
    Hitung masa kerja dalam tahun dan bulan.
    Returns: (tahun, bulan)
    """
    if not join_date:
        return 0, 0
    if isinstance(join_date, str):
        join_date = datetime.strptime(join_date, "%Y-%m-%d").date()
    end = end_date or date.today()
    tahun = end.year - join_date.year
    bulan = end.month - join_date.month
    if bulan < 0:
        tahun -= 1
        bulan += 12
    return tahun, bulan


def format_masa_kerja(join_date, end_date=None):
    """Format masa kerja sebagai string: '2 tahun 3 bulan'"""
    tahun, bulan = hitung_masa_kerja(join_date, end_date)
    if tahun > 0 and bulan > 0:
        return f"{tahun} tahun {bulan} bulan"
    elif tahun > 0:
        return f"{tahun} tahun"
    elif bulan > 0:
        return f"{bulan} bulan"
    return "Kurang dari 1 bulan"


def hitung_hari_kerja(start_date, end_date, holiday_dates=None):
    """
    Hitung jumlah hari kerja (Senin-Jumat) tidak termasuk hari libur.
    """
    if holiday_dates is None:
        holiday_dates = []
    count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5 and current not in holiday_dates:
            count += 1
        current += timedelta(days=1)
    return count


def get_periode_bulan(tahun, bulan):
    """
    Dapatkan tanggal pertama dan terakhir dari bulan tertentu.
    Returns: (start_date, end_date)
    """
    first_day = date(tahun, bulan, 1)
    last_day = date(tahun, bulan, calendar.monthrange(tahun, bulan)[1])
    return first_day, last_day


def format_tanggal_indonesia(d):
    """Format tanggal ke format Indonesia: '25 Januari 2024'"""
    if not d:
        return "-"
    BULAN = [
        '', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d").date()
    return f"{d.day} {BULAN[d.month]} {d.year}"


def sisa_hari(end_date):
    """Hitung sisa hari hingga tanggal tertentu dari hari ini."""
    if not end_date:
        return None
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    return (end_date - date.today()).days


def is_weekend(d):
    """Cek apakah tanggal adalah hari weekend."""
    return d.weekday() >= 5


def get_bulan_list():
    """Return list nama bulan dalam bahasa Indonesia."""
    return [
        (1, 'Januari'), (2, 'Februari'), (3, 'Maret'), (4, 'April'),
        (5, 'Mei'), (6, 'Juni'), (7, 'Juli'), (8, 'Agustus'),
        (9, 'September'), (10, 'Oktober'), (11, 'November'), (12, 'Desember'),
    ]


def get_tahun_list(start=2020, end=None):
    """Return list tahun dari start sampai tahun ini."""
    if end is None:
        end = date.today().year + 1
    return list(range(start, end + 1))
