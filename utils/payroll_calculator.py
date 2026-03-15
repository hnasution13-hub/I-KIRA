"""
Payroll Calculator
Mendukung jenis pengupahan bulanan/mingguan/harian,
custom multiplier lembur, custom BPJS, custom denda.
"""
import calendar
from datetime import date, timedelta
from decimal import Decimal


class PayrollCalculator:

    # ── Default PP 36/2021 ────────────────────────────────────────────────────
    DEFAULT_LEMBUR_JAM1   = Decimal('1.5')
    DEFAULT_LEMBUR_JAM2   = Decimal('2.0')
    DEFAULT_LEMBUR_LIBUR  = Decimal('2.0')
    DEFAULT_BPJS_KES_PCT  = Decimal('1.0')
    DEFAULT_BPJS_TK_PCT   = Decimal('3.0')
    DEFAULT_DENDA_TELAT   = 50_000   # per jam

    @staticmethod
    def hitung_hari_kerja(start_date, end_date, holiday_dates=None, hari_kerja_per_minggu=5):
        """
        Hitung jumlah hari kerja, kurangi hari libur nasional.
        hari_kerja_per_minggu=5 → Senin–Jumat
        hari_kerja_per_minggu=6 → Senin–Sabtu
        """
        if holiday_dates is None:
            holiday_dates = []
        # weekday(): 0=Senin, 5=Sabtu, 6=Minggu
        max_weekday = 4 if hari_kerja_per_minggu == 5 else 5
        work_days = 0
        current = start_date
        while current <= end_date:
            if current.weekday() <= max_weekday and current not in holiday_dates:
                work_days += 1
            current += timedelta(days=1)
        return work_days

    @staticmethod
    def hitung_pph21(penghasilan_bruto_bulanan, status_pajak='TK/0'):
        """
        Hitung PPh21 berdasarkan PTKP dan tarif progresif sesuai PMK 168/2023.

        Basis penghitungan adalah penghasilan bruto bulanan (gaji pokok +
        semua tunjangan tetap), bukan hanya gaji pokok saja.
        Return nilai PPh21 per bulan. Jika ditanggung perusahaan, caller-nya
        yang set ke 0.

        Catatan: tunjangan tidak tetap (transport, makan) dikecualikan dari
        basis PPh21 sesuai peraturan — harus difilter sebelum memanggil fungsi ini.
        """
        PTKP = {
            'TK/0': 54_000_000, 'TK/1': 58_500_000,
            'TK/2': 63_000_000, 'TK/3': 67_500_000,
            'K/0':  58_500_000, 'K/1':  63_000_000,
            'K/2':  67_500_000, 'K/3':  72_000_000,
            'K/I/0': 63_000_000, 'K/I/1': 67_500_000,
            'K/I/2': 72_000_000, 'K/I/3': 76_500_000,
        }
        ptkp = PTKP.get(status_pajak, 54_000_000)
        # Penghasilan neto = bruto setahun - biaya jabatan (5%, max 6jt/th) - PTKP
        bruto_tahunan = penghasilan_bruto_bulanan * 12
        biaya_jabatan = min(bruto_tahunan * 0.05, 6_000_000)
        pkp = max(0, bruto_tahunan - biaya_jabatan - ptkp)

        if pkp <= 0:
            pph = 0
        elif pkp <= 60_000_000:
            pph = pkp * 0.05
        elif pkp <= 250_000_000:
            pph = (60_000_000 * 0.05) + ((pkp - 60_000_000) * 0.15)
        elif pkp <= 500_000_000:
            pph = (60_000_000 * 0.05) + (190_000_000 * 0.15) + ((pkp - 250_000_000) * 0.25)
        else:
            pph = (60_000_000 * 0.05) + (190_000_000 * 0.15) + \
                  (250_000_000 * 0.25) + ((pkp - 500_000_000) * 0.30)

        return round(pph / 12)

    @staticmethod
    def hitung_bpjs_kesehatan(gaji_pokok, pct=None):
        """BPJS Kesehatan karyawan. Default 1% dari gaji pokok (max 12jt)."""
        p = float(pct) if pct else 1.0
        return round(min(gaji_pokok, 12_000_000) * p / 100)

    @staticmethod
    def hitung_bpjs_ketenagakerjaan(gaji_pokok, pct=None):
        """BPJS TK karyawan (JHT 2% + JP 1% = 3%). Default 3%."""
        p = float(pct) if pct else 3.0
        return round(gaji_pokok * p / 100)

    @staticmethod
    def hitung_uang_lembur(gaji_pokok, jam_lembur, hari='weekday',
                           multiplier_jam1=None, multiplier_jam2=None,
                           multiplier_libur=None, tarif_per_jam_override=None):
        """
        Hitung upah lembur.
        Gunakan multiplier custom jika diisi, default PP 36/2021 jika tidak.
        """
        if tarif_per_jam_override and tarif_per_jam_override > 0:
            upah_per_jam = tarif_per_jam_override
        else:
            upah_per_jam = gaji_pokok / 173  # default PP 36/2021

        if jam_lembur <= 0:
            return 0

        m1 = float(multiplier_jam1) if multiplier_jam1 and float(multiplier_jam1) > 0 \
             else float(PayrollCalculator.DEFAULT_LEMBUR_JAM1)
        m2 = float(multiplier_jam2) if multiplier_jam2 and float(multiplier_jam2) > 0 \
             else float(PayrollCalculator.DEFAULT_LEMBUR_JAM2)
        ml = float(multiplier_libur) if multiplier_libur and float(multiplier_libur) > 0 \
             else float(PayrollCalculator.DEFAULT_LEMBUR_LIBUR)

        if hari == 'weekday':
            if jam_lembur <= 1:
                total = upah_per_jam * m1 * jam_lembur
            else:
                total = (upah_per_jam * m1) + (upah_per_jam * m2 * (jam_lembur - 1))
        else:
            if jam_lembur <= 7:
                total = upah_per_jam * ml * jam_lembur
            elif jam_lembur == 8:
                total = (upah_per_jam * ml * 7) + (upah_per_jam * (ml + 1))
            else:
                total = (upah_per_jam * ml * 7) + (upah_per_jam * (ml + 1)) + \
                        (upah_per_jam * (ml + 2) * (jam_lembur - 8))

        return round(total)

    @staticmethod
    def hitung_denda_telat(gaji_pokok, menit_telat, denda_per_jam=None):
        """Denda keterlambatan. Default Rp 50.000/jam."""
        tarif = denda_per_jam if denda_per_jam and denda_per_jam > 0 \
                else PayrollCalculator.DEFAULT_DENDA_TELAT
        return round((menit_telat / 60) * tarif)

    @staticmethod
    def hitung_potongan_absen(gaji_pokok, hari_absen, upah_harian_override=None):
        """Potongan absen = upah harian × hari absen."""
        upah_harian = upah_harian_override if upah_harian_override and upah_harian_override > 0 \
                      else gaji_pokok / 25
        return round(upah_harian * hari_absen)

    @staticmethod
    def hitung_thr(employee, salary_benefit):
        """
        Hitung THR sesuai PP No. 36/2021.
        >= 12 bulan = 1 bulan upah, 1-11 bulan = proporsional, < 1 bulan = 0.
        Upah acuan = gaji pokok + semua tunjangan tetap.
        """
        tahun, bulan = employee.masa_kerja
        total_bulan = (tahun * 12) + bulan

        if total_bulan < 1:
            return 0

        upah_acuan = (
            salary_benefit.gaji_pokok +
            salary_benefit.tunjangan_jabatan +
            salary_benefit.tunjangan_tempat_tinggal +
            salary_benefit.tunjangan_keahlian +
            salary_benefit.tunjangan_komunikasi +
            salary_benefit.tunjangan_kesehatan
        )

        if total_bulan >= 12:
            return round(upah_acuan)
        return round((total_bulan / 12) * upah_acuan)

    @classmethod
    def generate_slip_gaji(cls, employee, salary_benefit, periode,
                           attendance_summary, thr_override=None):
        """
        Generate data slip gaji lengkap.
        Otomatis pakai konfigurasi custom jika salary_benefit.custom_aktif = True.
        """
        sb = salary_benefit
        gaji_pokok = sb.gaji_pokok

        # ── Resolusi config custom vs default ─────────────────────────────────
        use_custom = sb.custom_aktif

        m_jam1  = sb.custom_lembur_jam1_multiplier  if use_custom else None
        m_jam2  = sb.custom_lembur_jam2_multiplier  if use_custom else None
        m_libur = sb.custom_lembur_libur_multiplier if use_custom else None
        bpjs_kes_pct = sb.custom_bpjs_kes_pct if use_custom else None
        bpjs_tk_pct  = sb.custom_bpjs_tk_pct  if use_custom else None
        denda_per_jam = sb.custom_denda_telat_per_jam if use_custom else None
        potongan_absen_per_hari = sb.custom_potongan_absen_per_hari if use_custom else None

        # ── Pendapatan ────────────────────────────────────────────────────────
        jam_lembur = float(attendance_summary.get('jam_lembur', 0))

        # All-In: gaji sudah mencakup semua, lembur tidak dihitung
        if getattr(sb, 'status_gaji', 'reguler') == 'all_in':
            upah_lembur = 0
            jam_lembur  = 0
        else:
            # Gunakan tarif per jam override jika diisi di form upah
            tarif_override = sb.lembur_tarif_per_jam if hasattr(sb, 'lembur_tarif_per_jam') and sb.lembur_tarif_per_jam and sb.lembur_tarif_per_jam > 0 else None
            upah_lembur = cls.hitung_uang_lembur(
                gaji_pokok, jam_lembur,
                multiplier_jam1=m_jam1,
                multiplier_jam2=m_jam2,
                multiplier_libur=m_libur,
                tarif_per_jam_override=tarif_override,
            )

        gaji_kotor = (
            gaji_pokok +
            sb.tunjangan_jabatan + sb.tunjangan_tempat_tinggal +
            sb.tunjangan_keahlian + sb.tunjangan_komunikasi + sb.tunjangan_kesehatan +
            sb.tunjangan_transport + sb.tunjangan_makan +
            sb.tunjangan_site + sb.tunjangan_kehadiran +
            upah_lembur
        )

        # ── Potongan ──────────────────────────────────────────────────────────
        menit_telat = attendance_summary.get('menit_telat', 0)
        hari_absen  = attendance_summary.get('hari_absen', 0)

        potongan_telat = cls.hitung_denda_telat(gaji_pokok, menit_telat,
                                                denda_per_jam=denda_per_jam)

        # Potongan absen: pakai override dari form jika ada, lalu custom, lalu default
        if sb.potongan_absensi and sb.potongan_absensi > 0:
            potongan_absen = sb.potongan_absensi * hari_absen
        else:
            potongan_absen = cls.hitung_potongan_absen(
                gaji_pokok, hari_absen,
                upah_harian_override=potongan_absen_per_hari or None
            )

        # BPJS — pakai override dari form jika ada
        bpjs_kes = sb.get_bpjs_kesehatan()
        bpjs_tk  = sb.get_bpjs_ketenagakerjaan()

        # PPh21 — basis: gaji pokok + tunjangan tetap (tunjangan tidak tetap dikecualikan)
        # sesuai PMK 168/2023. Tunjangan tidak tetap (transport, makan, site, kehadiran)
        # TIDAK masuk basis PPh21.
        if sb.pph21_ditanggung_perusahaan:
            pph21 = 0
        else:
            status_pajak = employee.ptkp if employee.ptkp else 'TK/0'
            penghasilan_bruto_pph21 = (
                gaji_pokok +
                sb.tunjangan_jabatan +
                sb.tunjangan_tempat_tinggal +
                sb.tunjangan_keahlian +
                sb.tunjangan_komunikasi +
                sb.tunjangan_kesehatan
            )
            pph21 = cls.hitung_pph21(penghasilan_bruto_pph21, status_pajak=status_pajak)

        potongan_lainnya = sb.potongan_lainnya or 0

        total_potongan = (potongan_telat + potongan_absen +
                          bpjs_kes + bpjs_tk + pph21 + potongan_lainnya)
        gaji_bersih = gaji_kotor - total_potongan

        # ── THR ───────────────────────────────────────────────────────────────
        thr = thr_override if thr_override is not None else \
              (sb.thr if sb.thr and sb.thr > 0 else cls.hitung_thr(employee, sb))

        return {
            'employee_id':   employee.id,
            'employee_nama': employee.nama,
            'employee_nik':  employee.nik,
            'department':    str(employee.department) if employee.department else '-',
            'jabatan':       str(employee.jabatan)    if employee.jabatan    else '-',
            'periode':       periode,
            'jenis_pengupahan': sb.jenis_pengupahan,
            'custom_aktif':  use_custom,
            # Pendapatan
            'gaji_pokok':               gaji_pokok,
            'tunjangan_jabatan':        sb.tunjangan_jabatan,
            'tunjangan_tempat_tinggal': sb.tunjangan_tempat_tinggal,
            'tunjangan_keahlian':       sb.tunjangan_keahlian,
            'tunjangan_komunikasi':     sb.tunjangan_komunikasi,
            'tunjangan_kesehatan':      sb.tunjangan_kesehatan,
            'tunjangan_transport':      sb.tunjangan_transport,
            'tunjangan_makan':          sb.tunjangan_makan,
            'tunjangan_site':           sb.tunjangan_site,
            'tunjangan_kehadiran':      sb.tunjangan_kehadiran,
            'upah_lembur':              upah_lembur,
            'gaji_kotor':               gaji_kotor,
            # Kehadiran
            'hari_kerja':  attendance_summary.get('hari_kerja', 0),
            'hari_hadir':  attendance_summary.get('hari_hadir', 0),
            'hari_absen':  hari_absen,
            'menit_telat': menit_telat,
            'jam_lembur':  jam_lembur,
            # Potongan
            'potongan_telat':       potongan_telat,
            'potongan_absen':       potongan_absen,
            'potongan_lainnya':     potongan_lainnya,
            'bpjs_kesehatan':       bpjs_kes,
            'bpjs_ketenagakerjaan': bpjs_tk,
            'pph21':                pph21,
            'pph21_ditanggung_perusahaan': sb.pph21_ditanggung_perusahaan,
            'status_pajak':         employee.ptkp or 'TK/0',
            'total_potongan':       total_potongan,
            # Take home
            'gaji_bersih': gaji_bersih,
            # Tunjangan lain
            'thr':           thr,
            'bonus_tahunan': sb.bonus_tahunan,
            # Bank
            'bank_name':         employee.nama_bank,
            'bank_account':      employee.no_rek,
            'bank_account_name': employee.nama_rek,
        }