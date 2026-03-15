from django.db import models
from apps.employees.models import Employee
from apps.core.models import Company


class SalaryBenefit(models.Model):
    """Komponen gaji dan tunjangan karyawan."""

    TUNJANGAN_ALAT_CHOICES = [
        ('',           '-- Tidak Ada --'),
        ('hour_meter', 'Hour Meter (HM)'),
        ('kilometer',  'Kilometer (KM)'),
    ]
    JENIS_PENGUPAHAN_CHOICES = [
        ('bulanan',  'Bulanan'),
        ('mingguan', 'Mingguan'),
        ('harian',   'Harian'),
    ]
    HARI_KERJA_CHOICES = [
        (5, '5 Hari (Senin–Jumat)'),
        (6, '6 Hari (Senin–Sabtu)'),
    ]
    STATUS_GAJI_CHOICES = [
        ('reguler', 'Reguler'),
        ('all_in',  'All-In'),
    ]

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_benefit')

    # ── DASAR UPAH ─────────────────────────────────────────────────────────────
    jenis_pengupahan    = models.CharField(max_length=10, choices=JENIS_PENGUPAHAN_CHOICES,
                                           default='bulanan', verbose_name='Jenis Pengupahan')
    hari_kerja_per_minggu = models.IntegerField(choices=HARI_KERJA_CHOICES, default=5,
                                                verbose_name='Hari Kerja per Minggu')
    status_gaji         = models.CharField(max_length=10, choices=STATUS_GAJI_CHOICES,
                                           default='reguler', verbose_name='Status Gaji',
                                           help_text='All-In: gaji sudah termasuk semua komponen, lembur tidak dihitung')
    gaji_pokok          = models.BigIntegerField(default=0, verbose_name='Gaji Pokok')

    # ── TUNJANGAN TETAP ────────────────────────────────────────────────────────
    tunjangan_jabatan        = models.BigIntegerField(default=0, verbose_name='Tunjangan Jabatan')
    tunjangan_tempat_tinggal = models.BigIntegerField(default=0, verbose_name='Tunjangan Tempat Tinggal')
    tunjangan_keahlian       = models.BigIntegerField(default=0, verbose_name='Tunjangan Keahlian')
    tunjangan_komunikasi     = models.BigIntegerField(default=0, verbose_name='Tunjangan Komunikasi')
    tunjangan_kesehatan      = models.BigIntegerField(default=0, verbose_name='Tunjangan Kesehatan')

    # ── TUNJANGAN TIDAK TETAP ──────────────────────────────────────────────────
    tunjangan_transport  = models.BigIntegerField(default=0, verbose_name='Tunjangan Transport')
    tunjangan_makan      = models.BigIntegerField(default=0, verbose_name='Tunjangan Makan')
    tunjangan_site       = models.BigIntegerField(default=0, verbose_name='Tunjangan Site')
    tunjangan_kehadiran  = models.BigIntegerField(default=0, verbose_name='Tunjangan Kehadiran')
    tunjangan_alat_tipe  = models.CharField(max_length=20, choices=TUNJANGAN_ALAT_CHOICES,
                                            blank=True, verbose_name='Tipe Tunjangan Alat')
    tunjangan_alat_rate  = models.BigIntegerField(default=0, verbose_name='Rate Tunjangan Alat (per satuan)')

    # ── POTONGAN ───────────────────────────────────────────────────────────────
    # BPJS — 0 = hitung otomatis dari gaji pokok, >0 = override manual
    bpjs_ketenagakerjaan_override = models.BigIntegerField(default=0,
        verbose_name='BPJS Ketenagakerjaan (override, 0=otomatis)')
    bpjs_kesehatan_override       = models.BigIntegerField(default=0,
        verbose_name='BPJS Kesehatan (override, 0=otomatis)')
    # PPh21
    pph21_ditanggung_perusahaan   = models.BooleanField(default=False,
        verbose_name='PPh21 Ditanggung Perusahaan')
    # Potongan manual
    potongan_absensi   = models.BigIntegerField(default=0, verbose_name='Potongan Absensi per Hari')
    potongan_lainnya   = models.BigIntegerField(default=0, verbose_name='Potongan Lainnya')

    # ── TUNJANGAN LAIN (Tahunan) ───────────────────────────────────────────────
    # THR: 0 = hitung otomatis dari masa kerja, >0 = override manual
    thr           = models.BigIntegerField(default=0, verbose_name='THR (override, 0=otomatis)')
    bonus_tahunan = models.BigIntegerField(default=0, verbose_name='Bonus Tahunan')

    # Tarif lembur per jam (override, 0 = gaji_pokok/173)
    lembur_tarif_per_jam = models.BigIntegerField(default=0, verbose_name='Tarif Lembur per Jam (override)')

    # ── PAYROLL CUSTOM ─────────────────────────────────────────────────────────
    # Semua 0/None = pakai default PP 36/2021
    custom_aktif                 = models.BooleanField(default=False,
        verbose_name='Gunakan Konfigurasi Payroll Custom')
    custom_lembur_jam1_multiplier = models.DecimalField(max_digits=4, decimal_places=2,
        default=0, verbose_name='Multiplier Lembur Jam ke-1 (default 1.5)')
    custom_lembur_jam2_multiplier = models.DecimalField(max_digits=4, decimal_places=2,
        default=0, verbose_name='Multiplier Lembur Jam ke-2 dst (default 2.0)')
    custom_lembur_libur_multiplier = models.DecimalField(max_digits=4, decimal_places=2,
        default=0, verbose_name='Multiplier Lembur Hari Libur (default 2.0)')
    custom_bpjs_kes_pct          = models.DecimalField(max_digits=5, decimal_places=2,
        default=0, verbose_name='% BPJS Kesehatan Karyawan (default 1%)')
    custom_bpjs_tk_pct           = models.DecimalField(max_digits=5, decimal_places=2,
        default=0, verbose_name='% BPJS TK Karyawan (default 3%)')
    custom_denda_telat_per_jam   = models.BigIntegerField(default=0,
        verbose_name='Denda Telat per Jam (default Rp 50.000)')
    custom_potongan_absen_per_hari = models.BigIntegerField(default=0,
        verbose_name='Potongan Absen per Hari (default upah harian)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Upah & Benefit'
        verbose_name_plural = 'Upah & Benefit'

    def __str__(self):
        return f"Upah - {self.employee.nama}"

    @property
    def total_tunjangan_tetap(self):
        return (
            self.tunjangan_jabatan + self.tunjangan_tempat_tinggal +
            self.tunjangan_keahlian + self.tunjangan_komunikasi +
            self.tunjangan_kesehatan
        )

    @property
    def total_tunjangan_tidak_tetap(self):
        return (
            self.tunjangan_transport + self.tunjangan_makan +
            self.tunjangan_site + self.tunjangan_kehadiran
        )

    @property
    def total_tunjangan(self):
        return self.total_tunjangan_tetap + self.total_tunjangan_tidak_tetap

    @property
    def total_take_home_pay(self):
        return self.gaji_pokok + self.total_tunjangan

    @property
    def upah_harian(self):
        """Upah harian berdasarkan jenis pengupahan dan hari kerja."""
        if not self.gaji_pokok:
            return 0
        if self.jenis_pengupahan == 'harian':
            return self.gaji_pokok
        if self.jenis_pengupahan == 'mingguan':
            return self.gaji_pokok / self.hari_kerja_per_minggu
        # bulanan
        divisor = 21 if self.hari_kerja_per_minggu == 5 else 25
        return self.gaji_pokok / divisor

    @property
    def upah_per_jam(self):
        """Upah per jam = gaji pokok / 173 (standar PP 36/2021)."""
        return self.gaji_pokok / 173 if self.gaji_pokok else 0

    @property
    def tunjangan_alat_label(self):
        return dict(self.TUNJANGAN_ALAT_CHOICES).get(self.tunjangan_alat_tipe, '-')

    def get_bpjs_kesehatan(self):
        """Kembalikan nilai BPJS Kesehatan — override jika diisi, otomatis jika 0."""
        if self.bpjs_kesehatan_override and self.bpjs_kesehatan_override > 0:
            return self.bpjs_kesehatan_override
        pct = float(self.custom_bpjs_kes_pct) if self.custom_aktif and self.custom_bpjs_kes_pct else 1.0
        return round(min(self.gaji_pokok, 12_000_000) * pct / 100)

    def get_bpjs_ketenagakerjaan(self):
        """Kembalikan nilai BPJS TK — override jika diisi, otomatis jika 0."""
        if self.bpjs_ketenagakerjaan_override and self.bpjs_ketenagakerjaan_override > 0:
            return self.bpjs_ketenagakerjaan_override
        pct = float(self.custom_bpjs_tk_pct) if self.custom_aktif and self.custom_bpjs_tk_pct else 3.0
        return round(self.gaji_pokok * pct / 100)


class Payroll(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'), ('APPROVED', 'Disetujui'),
        ('PAID', 'Sudah Dibayar'), ('CANCELLED', 'Dibatalkan'),
    ]
    company           = models.ForeignKey(Company, on_delete=models.CASCADE,
                                          related_name='payrolls', verbose_name='Perusahaan')
    periode           = models.CharField(max_length=7, verbose_name='Periode (YYYY-MM)')
    tanggal_generate  = models.DateTimeField(auto_now_add=True)
    jumlah_karyawan   = models.IntegerField(default=0)
    total_gaji_kotor  = models.BigIntegerField(default=0)
    total_tunjangan   = models.BigIntegerField(default=0)
    total_potongan    = models.BigIntegerField(default=0)
    total_gaji_bersih = models.BigIntegerField(default=0)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    approved_by       = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='approved_payrolls')
    approved_date     = models.DateTimeField(null=True, blank=True)
    payment_date      = models.DateField(null=True, blank=True)
    payment_method    = models.CharField(max_length=30, blank=True)
    keterangan        = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Payroll'
        verbose_name_plural = 'Payroll'
        ordering = ['-periode']
        unique_together = [['company', 'periode']]

    def __str__(self):
        return f"Payroll {self.periode}"


class PayrollDetail(models.Model):
    payroll  = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='details')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)

    # Pendapatan
    gaji_pokok               = models.BigIntegerField(default=0)
    tunjangan_jabatan        = models.BigIntegerField(default=0)
    tunjangan_tempat_tinggal = models.BigIntegerField(default=0)
    tunjangan_keahlian       = models.BigIntegerField(default=0)
    tunjangan_komunikasi     = models.BigIntegerField(default=0)
    tunjangan_kesehatan      = models.BigIntegerField(default=0)
    tunjangan_transport      = models.BigIntegerField(default=0)
    tunjangan_makan          = models.BigIntegerField(default=0)
    tunjangan_site           = models.BigIntegerField(default=0)
    tunjangan_kehadiran      = models.BigIntegerField(default=0)
    upah_lembur              = models.BigIntegerField(default=0)

    # Kehadiran
    hari_kerja  = models.IntegerField(default=0)
    hari_hadir  = models.IntegerField(default=0)
    hari_absen  = models.IntegerField(default=0)
    menit_telat = models.IntegerField(default=0)
    jam_lembur  = models.DecimalField(max_digits=5, decimal_places=1, default=0)

    # Potongan
    potongan_telat       = models.BigIntegerField(default=0)
    potongan_absen       = models.BigIntegerField(default=0)
    potongan_lainnya     = models.BigIntegerField(default=0)
    bpjs_kesehatan       = models.BigIntegerField(default=0)
    bpjs_ketenagakerjaan = models.BigIntegerField(default=0)
    pph21                = models.BigIntegerField(default=0)

    # Total
    gaji_kotor     = models.BigIntegerField(default=0)
    total_potongan = models.BigIntegerField(default=0)
    gaji_bersih    = models.BigIntegerField(default=0)

    class Meta:
        verbose_name = 'Detail Payroll'
        verbose_name_plural = 'Detail Payroll'
        unique_together = ['payroll', 'employee']

    def __str__(self):
        return f"{self.payroll.periode} - {self.employee.nama}"

class SitePayrollSummary(models.Model):
    """
    Ringkasan payroll per Job Site per periode.
    Di-generate otomatis saat payroll di-approve.
    Basis untuk laporan multi-site payroll (P3.4).
    """
    payroll         = models.ForeignKey(Payroll, on_delete=models.CASCADE,
                                        related_name='site_summaries')
    job_site        = models.ForeignKey('employees.JobSite', on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='payroll_summaries',
                                        verbose_name='Job Site')
    site_label      = models.CharField(max_length=100, default='Kantor Pusat / Tidak Ada Site',
                                       verbose_name='Label Site')
    jumlah_karyawan = models.IntegerField(default=0)
    total_gaji_kotor  = models.BigIntegerField(default=0)
    total_tunjangan   = models.BigIntegerField(default=0)
    total_potongan    = models.BigIntegerField(default=0)
    total_gaji_bersih = models.BigIntegerField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Site Payroll Summary'
        verbose_name_plural = 'Site Payroll Summaries'
        ordering            = ['site_label']
        unique_together     = ['payroll', 'job_site']

    def __str__(self):
        return f'{self.site_label} — {self.payroll.periode}'

class SiteAllowanceRule(models.Model):
    """
    Aturan tunjangan site — diterapkan saat payroll_generate berdasarkan job_site karyawan.
    P3.4 Multi-site payroll.
    """
    JENIS_CHOICES = [
        ('flat',   'Nominal Tetap (Rp)'),
        ('persen', 'Persentase Gaji Pokok (%)'),
    ]
    company     = models.ForeignKey('core.Company', on_delete=models.CASCADE,
                                     related_name='site_allowance_rules')
    job_site    = models.ForeignKey('employees.JobSite', on_delete=models.CASCADE,
                                     related_name='allowance_rules', verbose_name='Job Site')
    jabatan     = models.ForeignKey('core.Position', on_delete=models.SET_NULL,
                                     null=True, blank=True, verbose_name='Jabatan (opsional)',
                                     help_text='Kosongkan = berlaku untuk semua jabatan di site ini')
    nama_komponen = models.CharField(max_length=100, default='Tunjangan Site',
                                      verbose_name='Nama Komponen')
    nilai       = models.BigIntegerField(default=0, verbose_name='Nilai (Rp atau %)')
    jenis       = models.CharField(max_length=10, choices=JENIS_CHOICES, default='flat',
                                    verbose_name='Jenis')
    aktif       = models.BooleanField(default=True, verbose_name='Aktif')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Site Allowance Rule'
        verbose_name_plural = 'Site Allowance Rules'
        ordering            = ['job_site', 'jabatan']

    def __str__(self):
        jabatan_str = f' / {self.jabatan}' if self.jabatan else ''
        return f'{self.job_site}{jabatan_str} — {self.nama_komponen} ({self.get_jenis_display()})'
