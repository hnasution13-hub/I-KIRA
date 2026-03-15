"""
Number utility functions untuk HRIS SmartDesk
"""


def format_rupiah(amount, with_symbol=True):
    """
    Format angka menjadi format Rupiah Indonesia.
    Contoh: 1500000 -> 'Rp 1.500.000'
    """
    if amount is None:
        return 'Rp 0' if with_symbol else '0'
    try:
        amount = int(amount)
        formatted = f"{amount:,}".replace(",", ".")
        return f"Rp {formatted}" if with_symbol else formatted
    except (ValueError, TypeError):
        return 'Rp 0' if with_symbol else '0'


SATUAN = ['', 'satu', 'dua', 'tiga', 'empat', 'lima', 'enam', 'tujuh', 'delapan', 'sembilan',
          'sepuluh', 'sebelas']


def _terbilang_ratusan(n):
    if n < 12:
        return SATUAN[n]
    elif n < 20:
        return SATUAN[n - 10] + ' belas'
    elif n < 100:
        return SATUAN[n // 10] + ' puluh' + (' ' + SATUAN[n % 10] if n % 10 else '')
    else:
        ratus = 'seratus' if n // 100 == 1 else SATUAN[n // 100] + ' ratus'
        sisa = n % 100
        return ratus + (' ' + _terbilang_ratusan(sisa) if sisa else '')


def terbilang(angka):
    """
    Konversi angka ke teks bahasa Indonesia.
    Contoh: 1500000 -> 'satu juta lima ratus ribu rupiah'
    """
    if angka is None:
        return 'nol rupiah'
    try:
        angka = int(angka)
    except (ValueError, TypeError):
        return 'nol rupiah'

    if angka == 0:
        return 'nol rupiah'

    negatif = angka < 0
    angka = abs(angka)

    bagian = []
    miliar = angka // 1_000_000_000
    juta = (angka % 1_000_000_000) // 1_000_000
    ribu = (angka % 1_000_000) // 1_000
    sisa = angka % 1_000

    if miliar:
        teks = 'satu miliar' if miliar == 1 else _terbilang_ratusan(miliar) + ' miliar'
        bagian.append(teks)
    if juta:
        teks = 'satu juta' if juta == 1 else _terbilang_ratusan(juta) + ' juta'
        bagian.append(teks)
    if ribu:
        teks = 'seribu' if ribu == 1 else _terbilang_ratusan(ribu) + ' ribu'
        bagian.append(teks)
    if sisa:
        bagian.append(_terbilang_ratusan(sisa))

    result = ' '.join(bagian) + ' rupiah'
    if negatif:
        result = 'minus ' + result
    return result


def persen(bagian, total, desimal=1):
    """Hitung persentase dengan aman."""
    if not total:
        return 0
    return round((bagian / total) * 100, desimal)


def bulatkan_ribuan(angka):
    """Bulatkan ke ribuan terdekat."""
    return round(angka / 1000) * 1000


def upah_per_jam(gaji_pokok, jam_kerja_sebulan=173):
    """Hitung upah per jam dari gaji pokok."""
    if not gaji_pokok or jam_kerja_sebulan == 0:
        return 0
    return gaji_pokok / jam_kerja_sebulan


def upah_harian(gaji_pokok, hari_kerja_sebulan=25):
    """Hitung upah harian dari gaji pokok."""
    if not gaji_pokok or hari_kerja_sebulan == 0:
        return 0
    return gaji_pokok / hari_kerja_sebulan
