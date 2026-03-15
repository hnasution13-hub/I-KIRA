"""
utils/sp_rules.py

Aturan dan mapping pelanggaran untuk Surat Peringatan (SP).
Berisi:
  - PELANGGARAN_MAP   : dict kode → detail pelanggaran
  - TINGKAT_TO_SP     : dict tingkat → level SP default
  - SP_LEVEL_LABEL    : dict level int → label string
  - get_sp_level_suggestion()  : saran level SP berdasarkan riwayat
  - get_pelanggaran_by_kategori() : grouping pelanggaran per kategori
"""

# ──────────────────────────────────────────────────────────────────────────────
#  LABEL SP
# ──────────────────────────────────────────────────────────────────────────────

SP_LEVEL_LABEL = {
    1: 'Surat Peringatan I (SP I)',
    2: 'Surat Peringatan II (SP II)',
    3: 'Surat Peringatan III (SP III)',
}


# ──────────────────────────────────────────────────────────────────────────────
#  MAPPING TINGKAT → LEVEL SP DEFAULT
# ──────────────────────────────────────────────────────────────────────────────

TINGKAT_TO_SP = {
    'Ringan': 1,
    'Sedang': 2,
    'Berat':  3,
}


# ──────────────────────────────────────────────────────────────────────────────
#  PELANGGARAN MAP
#  Format setiap entry:
#    'KODE': {
#        'label'      : str   – nama pelanggaran
#        'kategori'   : str   – kelompok pelanggaran
#        'tingkat'    : str   – Ringan / Sedang / Berat
#        'dasar_pasal': str   – referensi pasal/peraturan (opsional)
#    }
# ──────────────────────────────────────────────────────────────────────────────

PELANGGARAN_MAP = {

    # ── Kehadiran & Disiplin ──────────────────────────────────────────────────
    'KH-001': {
        'label'      : 'Terlambat masuk kerja berulang (> 3 kali dalam sebulan)',
        'kategori'   : 'Kehadiran & Disiplin',
        'tingkat'    : 'Ringan',
        'dasar_pasal': 'Pasal Tata Tertib Perusahaan Bab III ayat 1',
    },
    'KH-002': {
        'label'      : 'Tidak masuk kerja tanpa keterangan (alpha)',
        'kategori'   : 'Kehadiran & Disiplin',
        'tingkat'    : 'Ringan',
        'dasar_pasal': 'Pasal Tata Tertib Perusahaan Bab III ayat 2',
    },
    'KH-003': {
        'label'      : 'Meninggalkan area kerja tanpa izin atasan',
        'kategori'   : 'Kehadiran & Disiplin',
        'tingkat'    : 'Ringan',
        'dasar_pasal': 'Pasal Tata Tertib Perusahaan Bab III ayat 3',
    },
    'KH-004': {
        'label'      : 'Tidak masuk kerja ≥ 5 hari berturut-turut tanpa keterangan',
        'kategori'   : 'Kehadiran & Disiplin',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'UU Ketenagakerjaan No. 13/2003 Pasal 168',
    },

    # ── Kinerja & Produktivitas ───────────────────────────────────────────────
    'KN-001': {
        'label'      : 'Tidak memenuhi target kinerja yang ditetapkan',
        'kategori'   : 'Kinerja & Produktivitas',
        'tingkat'    : 'Ringan',
        'dasar_pasal': 'Peraturan Perusahaan Bab IV ayat 1',
    },
    'KN-002': {
        'label'      : 'Lalai dalam menjalankan tugas sehingga merugikan perusahaan',
        'kategori'   : 'Kinerja & Produktivitas',
        'tingkat'    : 'Sedang',
        'dasar_pasal': 'Peraturan Perusahaan Bab IV ayat 2',
    },
    'KN-003': {
        'label'      : 'Menolak perintah kerja yang layak dari atasan',
        'kategori'   : 'Kinerja & Produktivitas',
        'tingkat'    : 'Sedang',
        'dasar_pasal': 'Peraturan Perusahaan Bab IV ayat 3',
    },

    # ── Perilaku & Etika ──────────────────────────────────────────────────────
    'PE-001': {
        'label'      : 'Bersikap tidak sopan kepada rekan kerja atau atasan',
        'kategori'   : 'Perilaku & Etika',
        'tingkat'    : 'Ringan',
        'dasar_pasal': 'Kode Etik Perusahaan Pasal 2',
    },
    'PE-002': {
        'label'      : 'Perkelahian atau tindakan kekerasan fisik di lingkungan kerja',
        'kategori'   : 'Perilaku & Etika',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'Kode Etik Perusahaan Pasal 3',
    },
    'PE-003': {
        'label'      : 'Pelecehan verbal atau intimidasi terhadap rekan kerja',
        'kategori'   : 'Perilaku & Etika',
        'tingkat'    : 'Sedang',
        'dasar_pasal': 'Kode Etik Perusahaan Pasal 4',
    },
    'PE-004': {
        'label'      : 'Pelecehan seksual di lingkungan kerja',
        'kategori'   : 'Perilaku & Etika',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'UU No. 12 Tahun 2022 tentang TPKS',
    },

    # ── Aset & Fasilitas ──────────────────────────────────────────────────────
    'AS-001': {
        'label'      : 'Penggunaan aset perusahaan untuk kepentingan pribadi tanpa izin',
        'kategori'   : 'Aset & Fasilitas',
        'tingkat'    : 'Ringan',
        'dasar_pasal': 'Peraturan Perusahaan Bab VI ayat 1',
    },
    'AS-002': {
        'label'      : 'Merusak atau menghilangkan aset perusahaan akibat kelalaian',
        'kategori'   : 'Aset & Fasilitas',
        'tingkat'    : 'Sedang',
        'dasar_pasal': 'Peraturan Perusahaan Bab VI ayat 2',
    },
    'AS-003': {
        'label'      : 'Pencurian atau penggelapan aset perusahaan',
        'kategori'   : 'Aset & Fasilitas',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'KUHP Pasal 362 & Peraturan Perusahaan Bab VI ayat 3',
    },

    # ── Kerahasiaan & Informasi ───────────────────────────────────────────────
    'KR-001': {
        'label'      : 'Membocorkan informasi rahasia perusahaan kepada pihak luar',
        'kategori'   : 'Kerahasiaan & Informasi',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'Perjanjian Kerahasiaan (NDA) & UU ITE',
    },
    'KR-002': {
        'label'      : 'Mengakses sistem atau data tanpa otorisasi',
        'kategori'   : 'Kerahasiaan & Informasi',
        'tingkat'    : 'Sedang',
        'dasar_pasal': 'UU ITE No. 11/2008 jo. No. 19/2016 Pasal 30',
    },

    # ── Keselamatan Kerja (K3) ────────────────────────────────────────────────
    'K3-001': {
        'label'      : 'Melanggar prosedur keselamatan kerja (K3)',
        'kategori'   : 'Keselamatan Kerja (K3)',
        'tingkat'    : 'Sedang',
        'dasar_pasal': 'UU No. 1/1970 tentang Keselamatan Kerja',
    },
    'K3-002': {
        'label'      : 'Tidak menggunakan APD yang diwajibkan',
        'kategori'   : 'Keselamatan Kerja (K3)',
        'tingkat'    : 'Ringan',
        'dasar_pasal': 'Permenaker No. 8/2010 tentang APD',
    },
    'K3-003': {
        'label'      : 'Tindakan yang membahayakan keselamatan diri sendiri atau orang lain',
        'kategori'   : 'Keselamatan Kerja (K3)',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'UU No. 1/1970 Pasal 12',
    },

    # ── Keuangan & Administrasi ───────────────────────────────────────────────
    'KU-001': {
        'label'      : 'Pemalsuan dokumen atau laporan perusahaan',
        'kategori'   : 'Keuangan & Administrasi',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'KUHP Pasal 263 & Peraturan Perusahaan Bab VII',
    },
    'KU-002': {
        'label'      : 'Korupsi, suap, atau gratifikasi',
        'kategori'   : 'Keuangan & Administrasi',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'UU No. 31/1999 jo. No. 20/2001 tentang Tipikor',
    },
    'KU-003': {
        'label'      : 'Penggunaan dana perusahaan tidak sesuai peruntukan',
        'kategori'   : 'Keuangan & Administrasi',
        'tingkat'    : 'Sedang',
        'dasar_pasal': 'Peraturan Perusahaan Bab VII ayat 3',
    },

    # ── Pelanggaran Berat Lainnya ─────────────────────────────────────────────
    'PB-001': {
        'label'      : 'Membawa, menggunakan, atau mengedarkan narkoba di tempat kerja',
        'kategori'   : 'Pelanggaran Berat',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'UU No. 35/2009 tentang Narkotika',
    },
    'PB-002': {
        'label'      : 'Penghasutan atau provokasi yang mengganggu ketertiban perusahaan',
        'kategori'   : 'Pelanggaran Berat',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'Peraturan Perusahaan Bab VIII ayat 1',
    },
    'PB-003': {
        'label'      : 'Mogok kerja tidak sah / di luar prosedur yang berlaku',
        'kategori'   : 'Pelanggaran Berat',
        'tingkat'    : 'Berat',
        'dasar_pasal': 'UU No. 13/2003 Pasal 139–145',
    },
}


# ──────────────────────────────────────────────────────────────────────────────
#  FUNGSI HELPER
# ──────────────────────────────────────────────────────────────────────────────

def get_pelanggaran_by_kategori():
    """
    Kembalikan dict { kategori: [ {kode, ...entry} ] }
    untuk keperluan grouping di template.
    """
    result = {}
    for kode, entry in PELANGGARAN_MAP.items():
        kat = entry.get('kategori', 'Lain-lain')
        if kat not in result:
            result[kat] = []
        result[kat].append({'kode': kode, **entry})
    return result


def get_sp_level_suggestion(kode_pelanggaran: str, sp_aktif: list) -> dict:
    """
    Sarankan level SP berdasarkan:
      - tingkat pelanggaran dari PELANGGARAN_MAP
      - riwayat SP aktif karyawan (list of int level)

    Return dict:
      {
        'level'      : int       – level SP yang disarankan (1/2/3)
        'label'      : str       – label SP
        'reason'     : str       – alasan saran
        'tingkat'    : str       – tingkat pelanggaran
        'warn_phk'   : bool      – True jika sudah SP3 aktif
      }
    """
    rule = PELANGGARAN_MAP.get(kode_pelanggaran, {})
    tingkat = rule.get('tingkat', 'Ringan')

    # Level dasar berdasarkan tingkat pelanggaran
    base_level = TINGKAT_TO_SP.get(tingkat, 1)

    # Eskalasi berdasarkan SP aktif yang sudah ada
    if sp_aktif:
        max_aktif = max(sp_aktif)
        suggested = min(max_aktif + 1, 3)
        # Ambil yang lebih tinggi antara base level dan eskalasi
        level = max(base_level, suggested)
    else:
        level = base_level

    level = min(level, 3)  # tidak boleh > 3

    warn_phk = (3 in sp_aktif)

    if warn_phk:
        reason = (
            'Karyawan sudah memiliki SP III aktif. '
            'Pertimbangkan proses PHK sesuai peraturan yang berlaku.'
        )
    elif sp_aktif:
        reason = (
            f'Karyawan memiliki SP aktif (level {", ".join(str(s) for s in sorted(sp_aktif))}). '
            f'Disarankan eskalasi ke {SP_LEVEL_LABEL.get(level, f"SP {level}")}.'
        )
    else:
        reason = (
            f'Pelanggaran tingkat {tingkat}. '
            f'Disarankan dimulai dari {SP_LEVEL_LABEL.get(level, f"SP {level}")}.'
        )

    return {
        'level'   : level,
        'label'   : SP_LEVEL_LABEL.get(level, f'SP {level}'),
        'reason'  : reason,
        'tingkat' : tingkat,
        'warn_phk': warn_phk,
    }
