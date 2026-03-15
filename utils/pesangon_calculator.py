"""
utils/pesangon_calculator.py

Pesangon Calculator — PP No. 35/2021 (UU Cipta Kerja No. 11/2020)

Perubahan:
  - UPH 15% DIHAPUS (tidak berlaku lagi sesuai instruksi)
  - Logika dasar_pasal: HR pilih pasal PHK, sistem hitung otomatis
  - Uang Pisah: dummy policy (kebijakan perusahaan), kelipatan masa kerja
  - Kompensasi PKWT: UU No.11/2020 Pasal 61A — (masa_kerja_bulan / 12) × upah
"""
from datetime import date
from decimal import Decimal


# ─────────────────────────────────────────────────────────────────────────────
# DAFTAR PASAL & FORMULA (PP No. 35/2021)
# ─────────────────────────────────────────────────────────────────────────────

PASAL_CHOICES = [
    # (kode, label_tampil, faktor_up, faktor_upmk, pakai_uang_pisah)
    ('61A',        'UU 11/2020 Ps. 61A — Kompensasi PKWT',        0,    0,    False),  # khusus PKWT
    ('PP35_41',    'PP 35/2021 Ps. 41 — PHK karena efisiensi',    1.0,  1.0,  False),
    ('PP35_42_2',  'PP 35/2021 Ps. 42 Ay.2 — Perusahaan tutup, rugi',  0.5, 1.0, False),
    ('PP35_43_1',  'PP 35/2021 Ps. 43 Ay.1 — Force majeure, tidak PHK', 0.5, 1.0, False),
    ('PP35_43_2',  'PP 35/2021 Ps. 43 Ay.2 — Force majeure, PHK',  1.0, 1.0,  False),
    ('PP35_44_1',  'PP 35/2021 Ps. 44 Ay.1 — Penggabungan, tidak mau pindah', 0.5, 1.0, False),
    ('PP35_44_2',  'PP 35/2021 Ps. 44 Ay.2 — Penggabungan, PHK',   1.0, 1.0,  False),
    ('PP35_45_1',  'PP 35/2021 Ps. 45 Ay.1 — Pengambilalihan, tidak mau', 0.5, 1.0, False),
    ('PP35_45_2',  'PP 35/2021 Ps. 45 Ay.2 — Pengambilalihan, PHK', 0.75, 1.0, False),
    ('PP35_46_1',  'PP 35/2021 Ps. 46 Ay.1 — Perubahan status, tidak mau', 0.5, 1.0, False),
    ('PP35_46_2',  'PP 35/2021 Ps. 46 Ay.2 — Perubahan status, PHK', 1.0, 1.0, False),
    ('PP35_47',    'PP 35/2021 Ps. 47 — Pensiun',                  0.5,  1.0,  False),
    ('PP35_48',    'PP 35/2021 Ps. 48 — Meninggal dunia',          1.0,  1.0,  False),
    ('PP35_49',    'PP 35/2021 Ps. 49 — Karyawan sakit berkepanjangan', 0, 0, True),
    ('PP35_50',    'PP 35/2021 Ps. 50 — Karyawan ditahan & terbukti', 0,  0,   True),
    ('PP35_51',    'PP 35/2021 Ps. 51 — Karyawan ditahan & tidak terbukti', 0, 0, True),
    ('PP35_52_1',  'PP 35/2021 Ps. 52 Ay.1 — Pelanggaran berat (proses PHK)', 0.5, 1.0, False),
    ('PP35_52_2',  'PP 35/2021 Ps. 52 Ay.2 — Pelanggaran berat (terbukti)',  0,   0,   True),
    ('PP35_54_1',  'PP 35/2021 Ps. 54 Ay.1 — Mengundurkan diri',   0,    0,   True),
    ('PP35_54_2',  'PP 35/2021 Ps. 54 Ay.2 — Kontrak habis (tidak diperpanjang)', 0, 1.0, False),
    ('PP35_54_4',  'PP 35/2021 Ps. 54 Ay.4 — Pensiun (tanpa JHT cukup)', 0, 0, True),
    ('PP35_54_5',  'PP 35/2021 Ps. 54 Ay.5 — Pensiun (JHT ada)',   0,    1.0,  False),
    ('PP35_55',    'PP 35/2021 Ps. 55 — PHK sepihak perusahaan',    2.0,  1.0,  False),
    ('PP35_56',    'PP 35/2021 Ps. 56 — Karyawan mengajukan PHK (alasan penting)', 1.75, 1.0, False),
    ('PP35_57',    'PP 35/2021 Ps. 57 — PHK massal',                2.0,  1.0,  False),
]

# Dict untuk lookup cepat
PASAL_MAP = {p[0]: {'label': p[1], 'faktor_up': p[2], 'faktor_upmk': p[3], 'pakai_uang_pisah': p[4]}
             for p in PASAL_CHOICES}


# ─────────────────────────────────────────────────────────────────────────────
# MASA KERJA
# ─────────────────────────────────────────────────────────────────────────────

class MasaKerja:

    @staticmethod
    def hitung(join_date, end_date=None):
        """Hitung masa kerja dalam tahun dan bulan."""
        if not join_date:
            return 0, 0
        if isinstance(join_date, str):
            from datetime import datetime
            join_date = datetime.strptime(join_date, "%Y-%m-%d").date()
        end = end_date or date.today()
        tahun = end.year - join_date.year
        bulan = end.month - join_date.month
        if bulan < 0:
            tahun -= 1
            bulan += 12
        return tahun, bulan

    @staticmethod
    def total_bulan(join_date, end_date=None):
        tahun, bulan = MasaKerja.hitung(join_date, end_date)
        return tahun * 12 + bulan

    @staticmethod
    def kategori(tahun):
        if tahun < 1:
            return "Kurang dari 1 tahun"
        elif tahun < 3:
            return "1 - 3 tahun"
        elif tahun < 5:
            return "3 - 5 tahun"
        elif tahun < 8:
            return "5 - 8 tahun"
        elif tahun < 10:
            return "8 - 10 tahun"
        else:
            return "Lebih dari 10 tahun"

    @staticmethod
    def pengali_pesangon(tahun):
        """
        Pengali Uang Pesangon (UP) sesuai PP No. 35/2021 Pasal 40 ayat (2).
        < 1 th  = 1 bulan upah
        1–2 th  = 2 bulan upah
        3–4 th  = 3 bulan upah
        4–5 th  = 4 bulan upah  (bukan 3–5)
        5–6 th  = 5 bulan upah
        6–7 th  = 6 bulan upah
        7–8 th  = 7 bulan upah
        ≥ 8 th  = 9 bulan upah
        """
        if tahun < 1:
            return 1
        elif tahun < 2:
            return 2
        elif tahun < 3:
            return 3
        elif tahun < 4:
            return 4
        elif tahun < 5:
            return 5
        elif tahun < 6:
            return 6
        elif tahun < 7:
            return 7
        elif tahun < 8:
            return 8
        else:
            return 9


# ─────────────────────────────────────────────────────────────────────────────
# UANG PENGHARGAAN MASA KERJA (UPMK)
# ─────────────────────────────────────────────────────────────────────────────

def hitung_upmk(tahun, total_upah):
    """
    Hitung UPMK berdasarkan PP No. 35/2021 Pasal 43.
    3–6 th   = 2 bulan upah
    6–9 th   = 3 bulan upah
    9–12 th  = 4 bulan upah
    12–15 th = 5 bulan upah
    15–18 th = 6 bulan upah
    18–21 th = 7 bulan upah
    21–24 th = 8 bulan upah
    ≥ 24 th  = 10 bulan upah
    """
    if tahun < 3:
        return 0
    elif tahun < 6:
        return 2 * total_upah
    elif tahun < 9:
        return 3 * total_upah
    elif tahun < 12:
        return 4 * total_upah
    elif tahun < 15:
        return 5 * total_upah
    elif tahun < 18:
        return 6 * total_upah
    elif tahun < 21:
        return 7 * total_upah
    elif tahun < 24:
        return 8 * total_upah
    else:
        return 10 * total_upah


# ─────────────────────────────────────────────────────────────────────────────
# UANG PISAH — DUMMY POLICY (Kebijakan Perusahaan)
# ─────────────────────────────────────────────────────────────────────────────

def hitung_uang_pisah(tahun, total_upah):
    """
    Uang Pisah — Kebijakan Perusahaan (dummy, bukan ketetapan UU).
    < 1 th   = 0
    1–3 th   = 1 × upah
    3–6 th   = 2 × upah
    6–9 th   = 3 × upah
    9–12 th  = 4 × upah
    12–15 th = 5 × upah
    ≥ 15 th  = 6 × upah
    """
    if tahun < 1:
        return 0
    elif tahun < 3:
        return 1 * total_upah
    elif tahun < 6:
        return 2 * total_upah
    elif tahun < 9:
        return 3 * total_upah
    elif tahun < 12:
        return 4 * total_upah
    elif tahun < 15:
        return 5 * total_upah
    else:
        return 6 * total_upah


# ─────────────────────────────────────────────────────────────────────────────
# KOMPENSASI PKWT — UU No. 11/2020 Pasal 61A
# ─────────────────────────────────────────────────────────────────────────────

def hitung_kompensasi_pkwt(join_date, end_date, total_upah):
    """
    Kompensasi PKWT = (masa_kerja_bulan / 12) × total_upah
    Berlaku untuk karyawan berstatus PKWT.
    Minimum masa kerja 1 bulan untuk dapat kompensasi.
    """
    total_bulan = MasaKerja.total_bulan(join_date, end_date)
    if total_bulan < 1:
        return 0, 0
    kompensasi = round((total_bulan / 12) * total_upah)
    return kompensasi, total_bulan


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────

class PesangonCalculator:

    @classmethod
    def hitung(cls, gaji_pokok, tunjangan_tetap, join_date, tanggal_phk=None,
               alasan_phk='PHK Perusahaan', dasar_pasal=None, status_karyawan='PKWTT'):
        """
        Hitung pesangon lengkap berdasarkan UU Cipta Kerja & PP 35/2021.

        Args:
            gaji_pokok       : int/Decimal
            tunjangan_tetap  : int/Decimal
            join_date        : date
            tanggal_phk      : date | None  (default: hari ini)
            alasan_phk       : str  (legacy, dipakai jika dasar_pasal kosong)
            dasar_pasal      : str  kode pasal dari PASAL_MAP, e.g. 'PP35_55'
            status_karyawan  : str  'PKWT' | 'PKWTT' | dll

        Returns:
            dict lengkap berisi semua komponen pesangon
        """
        tahun, bulan = MasaKerja.hitung(join_date, tanggal_phk)
        total_upah   = int(gaji_pokok) + int(tunjangan_tetap)
        pengali_up   = MasaKerja.pengali_pesangon(tahun)

        # ── Tentukan faktor berdasarkan dasar_pasal ──────────────────────────
        pasal_info      = PASAL_MAP.get(dasar_pasal) if dasar_pasal else None
        pakai_uang_pisah = False
        is_pkwt_61a      = (dasar_pasal == '61A')

        if pasal_info:
            faktor_up   = pasal_info['faktor_up']
            faktor_upmk = pasal_info['faktor_upmk']
            pakai_uang_pisah = pasal_info['pakai_uang_pisah']
        else:
            # Legacy fallback — alasan_phk lama (backward compat)
            faktor_up, faktor_upmk = cls._faktor_legacy(alasan_phk)
            pakai_uang_pisah = (alasan_phk in ('Resign',))

        # ── Hitung komponen ──────────────────────────────────────────────────
        # Aturan utama:
        #   PKWT  → pesangon/upmk/uang_pisah SELALU 0, hanya kompensasi PKWT (Ps.61A)
        #   PKWTT → kompensasi_pkwt SELALU 0, hitung UP+UPMK/Uang Pisah sesuai pasal
        pesangon        = 0
        upmk            = 0
        uang_pisah      = 0
        kompensasi_pkwt = 0
        is_pkwt         = (status_karyawan == 'PKWT')

        if is_pkwt:
            # PKWT: hanya kompensasi Ps.61A — pesangon = 0
            kompensasi_pkwt, _ = hitung_kompensasi_pkwt(join_date, tanggal_phk, total_upah)
            total = kompensasi_pkwt
        else:
            # PKWTT/lainnya: pesangon sesuai pasal — kompensasi_pkwt = 0
            pesangon = round(total_upah * pengali_up * faktor_up)
            upmk_raw = hitung_upmk(tahun, total_upah)
            upmk     = round(upmk_raw * faktor_upmk)
            if pakai_uang_pisah:
                uang_pisah = hitung_uang_pisah(tahun, total_upah)
            total = pesangon + upmk + uang_pisah

        return {
            'masa_kerja_tahun'    : tahun,
            'masa_kerja_bulan'    : bulan,
            'masa_kerja_display'  : MasaKerja.kategori(tahun),
            'total_upah'          : total_upah,
            'pengali_pesangon'    : pengali_up,
            'faktor_up'           : faktor_up,
            'faktor_upmk'         : faktor_upmk,
            'dasar_pasal'         : dasar_pasal or '',
            'pasal_label'         : pasal_info['label'] if pasal_info else alasan_phk,
            'pesangon'            : pesangon,
            'upmk'                : upmk,
            'uang_pisah'          : uang_pisah,
            'pakai_uang_pisah'    : pakai_uang_pisah,
            'kompensasi_pkwt'     : kompensasi_pkwt,
            'is_pkwt_61a'         : is_pkwt_61a,
            'status_karyawan'     : status_karyawan,
            'total'               : total,
        }

    @staticmethod
    def _faktor_legacy(alasan_phk):
        """Backward-compat: faktor dari alasan_phk string lama."""
        mapping = {
            'PHK Perusahaan'  : (1.0, 1.0),
            'Resign'          : (0,   0),
            'Pensiun'         : (0.5, 1.0),
            'Meninggal'       : (1.0, 1.0),
            'Kontrak Habis'   : (0,   1.0),
            'Pelanggaran Berat': (0,  0),
        }
        return mapping.get(alasan_phk, (1.0, 1.0))
