from django.db import models
from apps.employees.models import Employee
from apps.core.models import Company


class Violation(models.Model):
    TIPE_CHOICES = [
        ('Surat Peringatan Lisan', 'Surat Peringatan Lisan'),
        ('Surat Peringatan 1', 'Surat Peringatan 1'),
        ('Surat Peringatan 2', 'Surat Peringatan 2'),
        ('Surat Peringatan 3', 'Surat Peringatan 3'),
        ('Perjanjian Bersama (PHK)', 'Perjanjian Bersama (PHK)'),
    ]
    TINGKAT_CHOICES = [
        ('Ringan', 'Ringan'),
        ('Sedang', 'Sedang'),
        ('Berat', 'Berat'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Proses', 'Dalam Proses'),
        ('Selesai', 'Selesai'),
        ('Dibatalkan', 'Dibatalkan'),
    ]

    company          = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='violations', verbose_name='Perusahaan')
    employee         = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='violations')
    tipe_pelanggaran = models.CharField(max_length=50, choices=TIPE_CHOICES)
    tanggal_kejadian = models.DateField(verbose_name='Tanggal Kejadian')
    deskripsi        = models.TextField(verbose_name='Deskripsi Pelanggaran')
    tingkat          = models.CharField(max_length=10, choices=TINGKAT_CHOICES, default='Ringan')
    poin             = models.IntegerField(default=0)
    sanksi           = models.TextField(blank=True, verbose_name='Sanksi')
    dokumen          = models.FileField(upload_to='violations/', null=True, blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Pelanggaran & Sanksi'
        verbose_name_plural = 'Pelanggaran & Sanksi'
        ordering            = ['-tanggal_kejadian']

    def __str__(self):
        return f"{self.employee.nama} - {self.tipe_pelanggaran} ({self.tanggal_kejadian})"


class Severance(models.Model):
    """
    Perhitungan pesangon berdasarkan PP No. 35/2021 & UU No.11/2020 (Cipta Kerja).
    UPH 15% sudah tidak berlaku — dihapus dari kalkulasi.
    Kompensasi PKWT mengacu Pasal 61A UU No.11/2020.
    Uang Pisah mengacu kebijakan perusahaan (dummy policy).
    """

    ALASAN_PHK_CHOICES = [
        ('Resign',            'Mengundurkan Diri'),
        ('PHK Perusahaan',    'PHK oleh Perusahaan'),
        ('Pensiun',           'Pensiun'),
        ('Meninggal',         'Meninggal Dunia'),
        ('Kontrak Habis',     'Kontrak Habis'),
        ('Pelanggaran Berat', 'Pelanggaran Berat'),
    ]

    company         = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='severances', verbose_name='Perusahaan')
    employee        = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='severances')
    tanggal_phk     = models.DateField(verbose_name='Tanggal PHK / Berakhir')
    alasan_phk      = models.CharField(max_length=30, choices=ALASAN_PHK_CHOICES)

    # Dasar pasal (PP 35/2021 / UU 11/2020)
    dasar_pasal     = models.CharField(max_length=20, blank=True, verbose_name='Dasar Pasal',
                                       help_text='Kode pasal, e.g. PP35_55, 61A')

    # Input upah
    gaji_pokok      = models.BigIntegerField(verbose_name='Gaji Pokok')
    tunjangan_tetap = models.BigIntegerField(default=0, verbose_name='Tunjangan Tetap')

    # Masa Kerja
    masa_kerja_tahun = models.IntegerField(default=0)
    masa_kerja_bulan = models.IntegerField(default=0)

    # Hasil Perhitungan
    total_upah          = models.BigIntegerField(default=0, verbose_name='Total Upah')
    pengali_pesangon    = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    pesangon            = models.BigIntegerField(default=0, verbose_name='Uang Pesangon (UP)')
    upmk                = models.BigIntegerField(default=0, verbose_name='Uang Penghargaan Masa Kerja (UPMK)')
    uang_pisah          = models.BigIntegerField(default=0, verbose_name='Uang Pisah (Kebijakan Perusahaan)')
    kompensasi_pkwt     = models.BigIntegerField(default=0, verbose_name='Kompensasi PKWT (Ps. 61A)')
    total_pesangon      = models.BigIntegerField(default=0, verbose_name='Total Pesangon')

    keterangan  = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Perhitungan Pesangon'
        verbose_name_plural = 'Perhitungan Pesangon'
        ordering            = ['-tanggal_phk']

    def __str__(self):
        return f"Pesangon — {self.employee.nama} ({self.tanggal_phk})"

    def hitung_pesangon(self):
        """Delegasi ke PesangonCalculator."""
        from utils.pesangon_calculator import PesangonCalculator
        result = PesangonCalculator.hitung(
            gaji_pokok       = self.gaji_pokok,
            tunjangan_tetap  = self.tunjangan_tetap,
            join_date        = self.employee.join_date,
            tanggal_phk      = self.tanggal_phk,
            alasan_phk       = self.alasan_phk,
            dasar_pasal      = self.dasar_pasal,
            status_karyawan  = self.employee.status_karyawan,
        )
        self.masa_kerja_tahun   = result['masa_kerja_tahun']
        self.masa_kerja_bulan   = result['masa_kerja_bulan']
        self.total_upah         = result['total_upah']
        self.pengali_pesangon   = result['pengali_pesangon']
        self.pesangon           = result['pesangon']
        self.upmk               = result['upmk']
        self.uang_pisah         = result['uang_pisah']
        self.kompensasi_pkwt    = result['kompensasi_pkwt']
        self.total_pesangon     = result['total']
        return self.total_pesangon


class PerjanjianBersama(models.Model):
    """
    Perjanjian Bersama (PB) PHK — dokumen kesepakatan antara perusahaan dan karyawan.
    Pipeline: Severance (pesangon) → PerjanjianBersama (PB) → Print dokumen.
    """

    STATUS_CHOICES = [
        ('draft',    'Draft'),
        ('final',    'Final / Ditandatangani'),
    ]

    # ── Relasi ────────────────────────────────────────────────────────────────
    company   = models.ForeignKey(Company,   on_delete=models.CASCADE, related_name='perjanjian_bersama')
    employee  = models.ForeignKey(Employee,  on_delete=models.CASCADE, related_name='perjanjian_bersama')
    severance = models.OneToOneField('Severance', on_delete=models.CASCADE,
                                     related_name='perjanjian_bersama', null=True, blank=True)

    # ── Metadata PB ───────────────────────────────────────────────────────────
    nomor_pb    = models.CharField(max_length=50, blank=True, verbose_name='Nomor PB')
    tanggal_pb  = models.DateField(verbose_name='Tanggal PB')
    tempat_pb   = models.CharField(max_length=200, blank=True, verbose_name='Tempat Penandatanganan')
    dasar_pasal = models.CharField(max_length=20, blank=True, verbose_name='Dasar Pasal')
    tanggal_phk = models.DateField(verbose_name='Tanggal PHK')
    alasan_phk  = models.CharField(max_length=30, blank=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')

    # ── Data karyawan (snapshot saat PB dibuat) ───────────────────────────────
    snap_nama          = models.CharField(max_length=200, blank=True)
    snap_nik           = models.CharField(max_length=20,  blank=True)
    snap_jabatan       = models.CharField(max_length=200, blank=True)
    snap_departemen    = models.CharField(max_length=200, blank=True)
    snap_tanggal_masuk = models.DateField(null=True, blank=True)
    snap_alamat        = models.TextField(blank=True)
    snap_gaji_pokok    = models.BigIntegerField(default=0)
    snap_status_karyawan = models.CharField(max_length=10, default='PKWTT')

    # ── Penandatangan perusahaan (bisa beda per PB) ───────────────────────────
    nama_penandatangan    = models.CharField(max_length=100, blank=True, verbose_name='Nama Pihak Pertama')
    jabatan_penandatangan = models.CharField(max_length=100, blank=True, verbose_name='Jabatan Pihak Pertama')

    # ── Komponen pesangon (dari Severance) ───────────────────────────────────
    total_pesangon   = models.BigIntegerField(default=0, verbose_name='Total Pesangon / Kompensasi')
    upmk             = models.BigIntegerField(default=0, verbose_name='UPMK')

    # ── Komponen tambahan (input manual) ─────────────────────────────────────
    sisa_cuti_tahunan  = models.IntegerField(default=0, verbose_name='Sisa Cuti Tahunan (hari)')
    nilai_cuti_tahunan = models.BigIntegerField(default=0)

    pakai_cuti_roster  = models.BooleanField(default=False)
    sisa_cuti_roster   = models.IntegerField(default=0, verbose_name='Sisa Cuti Roster (hari)')
    nilai_cuti_roster  = models.BigIntegerField(default=0)

    # Sisa gaji prorate
    tanggal_cut_off    = models.DateField(null=True, blank=True, verbose_name='Tanggal Cut-Off Gaji')
    sisa_hari_kerja    = models.IntegerField(default=0, verbose_name='Sisa Hari Kerja')
    nilai_sisa_gaji    = models.BigIntegerField(default=0, verbose_name='Sisa Gaji Prorate')

    # Uang transportasi (opsional, bukan tunjangan transport)
    pakai_uang_transport  = models.BooleanField(default=False)
    nilai_uang_transport  = models.BigIntegerField(default=0, verbose_name='Uang Transportasi (POH)')

    # ── Total akhir ───────────────────────────────────────────────────────────
    grand_total = models.BigIntegerField(default=0, verbose_name='Grand Total PB')
    terbilang   = models.TextField(blank=True, verbose_name='Terbilang')

    # ── Jadwal pembayaran (teks bebas) ────────────────────────────────────────
    jadwal_pembayaran = models.TextField(blank=True, verbose_name='Jadwal Pembayaran')
    catatan           = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Perjanjian Bersama PHK'
        verbose_name_plural = 'Perjanjian Bersama PHK'
        ordering            = ['-tanggal_pb']

    def __str__(self):
        return f'PB — {self.snap_nama} ({self.tanggal_phk})'

    def hitung_grand_total(self):
        is_pkwt = (self.snap_status_karyawan == 'PKWT')
        if is_pkwt:
            self.grand_total = (
                self.total_pesangon +   # kompensasi PKWT
                self.nilai_cuti_tahunan +
                (self.nilai_cuti_roster if self.pakai_cuti_roster else 0) +
                self.nilai_sisa_gaji +
                (self.nilai_uang_transport if self.pakai_uang_transport else 0)
            )
        else:
            self.grand_total = (
                self.total_pesangon +   # UP
                self.upmk +
                self.nilai_cuti_tahunan +
                (self.nilai_cuti_roster if self.pakai_cuti_roster else 0) +
                self.nilai_sisa_gaji +
                (self.nilai_uang_transport if self.pakai_uang_transport else 0)
            )
        from utils.number_utils import terbilang
        try:
            self.terbilang = terbilang(self.grand_total)
        except Exception:
            self.terbilang = ''
        return self.grand_total


# ══════════════════════════════════════════════════════════════════════════════
#  SURAT PERINGATAN
# ══════════════════════════════════════════════════════════════════════════════

class SuratPeringatan(models.Model):
    SP_LEVEL_CHOICES = [(1, 'SP I'), (2, 'SP II'), (3, 'SP III')]
    STATUS_CHOICES   = [
        ('aktif',   'Aktif'),
        ('expired', 'Expired'),
        ('dicabut', 'Dicabut'),
    ]

    company   = models.ForeignKey(Company,  on_delete=models.CASCADE, related_name='surat_peringatan')
    employee  = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='surat_peringatan')
    violation = models.ForeignKey('Violation', on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='surat_peringatan')

    # Level & Nomor
    level    = models.IntegerField(choices=SP_LEVEL_CHOICES, verbose_name='Level SP')
    nomor_sp = models.CharField(max_length=80, blank=True, verbose_name='Nomor Surat')

    # Dasar pelanggaran (dari PELANGGARAN_MAP)
    kode_pelanggaran     = models.CharField(max_length=10,  blank=True)
    label_pelanggaran    = models.CharField(max_length=300, blank=True, verbose_name='Jenis Pelanggaran')
    kategori_pelanggaran = models.CharField(max_length=100, blank=True, verbose_name='Kategori')
    tingkat_pelanggaran  = models.CharField(max_length=10,  blank=True, verbose_name='Tingkat')
    dasar_pasal          = models.CharField(max_length=100, blank=True, verbose_name='Dasar Pasal')

    # Tanggal
    tanggal_sp             = models.DateField(verbose_name='Tanggal SP')
    tanggal_berlaku_sampai = models.DateField(verbose_name='Berlaku Sampai')

    # Isi surat
    uraian_pelanggaran   = models.TextField(verbose_name='Uraian Pelanggaran Detail')
    sanksi               = models.TextField(blank=True, verbose_name='Sanksi')
    pernyataan_karyawan  = models.TextField(blank=True, verbose_name='Pernyataan Kesanggupan Karyawan')

    # Penandatangan
    nama_penandatangan    = models.CharField(max_length=100, blank=True)
    jabatan_penandatangan = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif')

    # Tracking eskalasi
    is_eskalasi    = models.BooleanField(default=False, verbose_name='Hasil Eskalasi')
    sp_sebelumnya  = models.ForeignKey('self', on_delete=models.SET_NULL,
                                       null=True, blank=True,
                                       related_name='eskalasi_berikutnya',
                                       verbose_name='SP Sebelumnya')

    catatan    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Surat Peringatan'
        verbose_name_plural = 'Surat Peringatan'
        ordering            = ['-tanggal_sp']

    def __str__(self):
        return f'SP{self.level} — {self.employee.nama} ({self.tanggal_sp})'

    @property
    def level_label(self):
        return dict(self.SP_LEVEL_CHOICES).get(self.level, f'SP{self.level}')

    @property
    def is_aktif(self):
        from django.utils import timezone
        return self.status == 'aktif' and self.tanggal_berlaku_sampai >= timezone.now().date()

    def generate_nomor(self):
        """Auto-generate nomor SP: SP-I/001/HRD/III/2026"""
        from django.utils import timezone
        level_str = {1: 'I', 2: 'II', 3: 'III'}.get(self.level, str(self.level))
        bulan_romawi = {
            1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',
            7:'VII',8:'VIII',9:'IX',10:'X',11:'XI',12:'XII'
        }
        now = timezone.now()
        # Hitung urutan SP level ini di company bulan ini
        urutan = SuratPeringatan.objects.filter(
            company=self.company,
            level=self.level,
            tanggal_sp__year=now.year,
            tanggal_sp__month=now.month,
        ).count() + 1
        return f'SP-{level_str}/{urutan:03d}/HRD/{bulan_romawi[now.month]}/{now.year}'


# ══════════════════════════════════════════════════════════════════════════════
#  SURAT PHK
# ══════════════════════════════════════════════════════════════════════════════

class SuratPHK(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('final', 'Final')]

    company            = models.ForeignKey(Company,  on_delete=models.CASCADE, related_name='surat_phk')
    employee           = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='surat_phk')
    perjanjian_bersama = models.OneToOneField(
        'PerjanjianBersama', on_delete=models.CASCADE,
        related_name='surat_phk', null=True, blank=True
    )

    # Metadata surat
    nomor_surat   = models.CharField(max_length=80, blank=True, verbose_name='Nomor Surat')
    tanggal_surat = models.DateField(verbose_name='Tanggal Surat')
    tempat_surat  = models.CharField(max_length=100, blank=True)

    # Snapshot data dari PB
    snap_nama          = models.CharField(max_length=200, blank=True)
    snap_nik           = models.CharField(max_length=20,  blank=True)
    snap_jabatan       = models.CharField(max_length=200, blank=True)
    snap_departemen    = models.CharField(max_length=200, blank=True)
    snap_tanggal_masuk = models.DateField(null=True, blank=True)
    snap_tanggal_phk   = models.DateField(null=True, blank=True)
    snap_alasan_phk    = models.CharField(max_length=100, blank=True)
    snap_dasar_pasal   = models.CharField(max_length=50,  blank=True)
    snap_grand_total   = models.BigIntegerField(default=0)
    snap_terbilang     = models.TextField(blank=True)

    # Isi surat
    dasar_hukum             = models.TextField(blank=True, verbose_name='Dasar Hukum PHK')
    alasan_phk              = models.TextField(blank=True, verbose_name='Alasan PHK')
    keterangan_kompensasi   = models.TextField(blank=True, verbose_name='Keterangan Kompensasi')
    catatan                 = models.TextField(blank=True)

    # Penandatangan
    nama_penandatangan    = models.CharField(max_length=100, blank=True)
    jabatan_penandatangan = models.CharField(max_length=100, blank=True)

    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Surat PHK'
        verbose_name_plural = 'Surat PHK'
        ordering            = ['-tanggal_surat']

    def __str__(self):
        return f'Surat PHK — {self.snap_nama} ({self.tanggal_surat})'

    def generate_nomor(self):
        from django.utils import timezone
        bulan_romawi = {
            1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',
            7:'VII',8:'VIII',9:'IX',10:'X',11:'XI',12:'XII'
        }
        now    = timezone.now()
        urutan = SuratPHK.objects.filter(
            company=self.company,
            tanggal_surat__year=now.year,
            tanggal_surat__month=now.month,
        ).count() + 1
        return f'PHK/{urutan:03d}/HRD/{bulan_romawi[now.month]}/{now.year}'

    def snapshot_dari_pb(self):
        """Isi snapshot dari PerjanjianBersama terkait."""
        pb = self.perjanjian_bersama
        if not pb:
            return
        self.snap_nama          = pb.snap_nama
        self.snap_nik           = pb.snap_nik
        self.snap_jabatan       = pb.snap_jabatan
        self.snap_departemen    = pb.snap_departemen
        self.snap_tanggal_masuk = pb.snap_tanggal_masuk
        self.snap_tanggal_phk   = pb.tanggal_phk
        self.snap_alasan_phk    = pb.alasan_phk
        self.snap_dasar_pasal   = pb.dasar_pasal
        self.snap_grand_total   = pb.grand_total
        self.snap_terbilang     = pb.terbilang


# ══════════════════════════════════════════════════════════════════════════════
#  SURAT KETERANGAN KERJA
# ══════════════════════════════════════════════════════════════════════════════

class SuratKeteranganKerja(models.Model):
    company  = models.ForeignKey(Company,  on_delete=models.CASCADE, related_name='skk')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='skk')

    # Metadata
    nomor_surat   = models.CharField(max_length=80, blank=True, verbose_name='Nomor Surat')
    tanggal_surat = models.DateField(verbose_name='Tanggal Surat')
    tujuan_surat  = models.CharField(max_length=200, blank=True, verbose_name='Tujuan Surat',
                                     help_text='Misal: keperluan KPR, melamar pekerjaan, beasiswa')

    # Snapshot data karyawan
    snap_nama           = models.CharField(max_length=200, blank=True)
    snap_nik            = models.CharField(max_length=20,  blank=True)
    snap_jabatan        = models.CharField(max_length=200, blank=True)
    snap_departemen     = models.CharField(max_length=200, blank=True)
    snap_tanggal_masuk  = models.DateField(null=True, blank=True)
    snap_tanggal_keluar = models.DateField(null=True, blank=True)
    snap_status         = models.CharField(max_length=20, blank=True)

    # Isi SKK
    masa_kerja_keterangan   = models.CharField(max_length=200, blank=True,
                                               verbose_name='Keterangan Masa Kerja')
    tampilkan_gaji          = models.BooleanField(default=False, verbose_name='Tampilkan Gaji')
    snap_gaji_pokok         = models.BigIntegerField(default=0)
    keterangan_tambahan     = models.TextField(blank=True)

    # Penandatangan
    nama_penandatangan    = models.CharField(max_length=100, blank=True)
    jabatan_penandatangan = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Surat Keterangan Kerja'
        verbose_name_plural = 'Surat Keterangan Kerja'
        ordering            = ['-tanggal_surat']

    def __str__(self):
        return f'SKK — {self.snap_nama} ({self.tanggal_surat})'

    def generate_nomor(self):
        from django.utils import timezone
        bulan_romawi = {
            1:'I',2:'II',3:'III',4:'IV',5:'V',6:'VI',
            7:'VII',8:'VIII',9:'IX',10:'X',11:'XI',12:'XII'
        }
        now    = timezone.now()
        urutan = SuratKeteranganKerja.objects.filter(
            company=self.company,
            tanggal_surat__year=now.year,
            tanggal_surat__month=now.month,
        ).count() + 1
        return f'SKK/{urutan:03d}/HRD/{bulan_romawi[now.month]}/{now.year}'

    def snapshot_dari_employee(self):
        """Isi snapshot dari data Employee."""
        emp = self.employee
        self.snap_nama          = emp.nama
        self.snap_nik           = emp.nik
        self.snap_jabatan       = str(emp.jabatan)    if emp.jabatan    else ''
        self.snap_departemen    = str(emp.department) if emp.department else ''
        self.snap_tanggal_masuk = emp.join_date
        self.snap_status        = emp.status_karyawan or ''
        self.snap_gaji_pokok    = 0
        # Hitung masa kerja
        if emp.join_date:
            from datetime import date
            today = self.snap_tanggal_keluar or date.today()
            delta_days  = (today - emp.join_date).days
            tahun       = delta_days // 365
            sisa_bulan  = (delta_days % 365) // 30
            parts = []
            if tahun:
                parts.append(f'{tahun} tahun')
            if sisa_bulan:
                parts.append(f'{sisa_bulan} bulan')
            self.masa_kerja_keterangan = ' '.join(parts) if parts else '< 1 bulan'
        # Ambil gaji dari salary benefit jika ada
        try:
            sb = emp.salary_benefits.filter(aktif=True).first()
            if sb:
                self.snap_gaji_pokok = sb.gaji_pokok or 0
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  PERATURAN PERUSAHAAN — DOKUMEN SP
# ══════════════════════════════════════════════════════════════════════════════

import os as _os

class PeraturanPerusahaanSP(models.Model):
    JENIS_CHOICES = [
        ('pdf',   'PDF Document'),
        ('docx',  'Word Document'),
        ('other', 'Lainnya'),
    ]

    company       = models.ForeignKey(Company, on_delete=models.CASCADE,
                                      related_name='pp_sp_docs', verbose_name='Perusahaan')
    judul         = models.CharField(max_length=255, verbose_name='Judul Dokumen')
    versi         = models.CharField(max_length=50, blank=True, verbose_name='Versi / Revisi')
    dokumen       = models.FileField(upload_to='pp_sp/', verbose_name='File Dokumen')
    jenis         = models.CharField(max_length=10, choices=JENIS_CHOICES, default='pdf')
    keterangan    = models.TextField(blank=True, verbose_name='Keterangan')
    is_aktif      = models.BooleanField(default=True, verbose_name='Aktif (berlaku)')
    diunggah_oleh = models.CharField(max_length=100, blank=True, verbose_name='Diunggah oleh')
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Peraturan Perusahaan SP'
        verbose_name_plural = 'Peraturan Perusahaan SP'
        ordering            = ['-created_at']

    def __str__(self):
        return f'{self.judul} ({self.versi or "v1"}) — {self.company}'

    @property
    def filename(self):
        return _os.path.basename(self.dokumen.name) if self.dokumen else ''

    @property
    def file_size_display(self):
        try:
            size = self.dokumen.size
            if size < 1024:       return f'{size} B'
            elif size < 1024**2:  return f'{size/1024:.1f} KB'
            else:                 return f'{size/1024**2:.1f} MB'
        except Exception:
            return '—'
