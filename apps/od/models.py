from django.db import models
from apps.core.models import Company, Department, Position


# ══════════════════════════════════════════════════════════════════════════════
#  WORKLOAD STANDARD — Standar beban kerja per jabatan
# ══════════════════════════════════════════════════════════════════════════════

class WorkloadStandard(models.Model):
    SATUAN_CHOICES = [
        ('jam/hari',   'Jam per Hari'),
        ('jam/minggu', 'Jam per Minggu'),
        ('unit/hari',  'Unit per Hari'),
        ('unit/bulan', 'Unit per Bulan'),
    ]

    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='workload_standards')
    jabatan    = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='workload_standards',
                                   verbose_name='Jabatan')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='workload_standards')

    nama_aktivitas  = models.CharField(max_length=200, verbose_name='Nama Aktivitas / Beban Kerja')
    standar_output  = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Standar Output')
    satuan          = models.CharField(max_length=15, choices=SATUAN_CHOICES, default='jam/hari')
    deskripsi       = models.TextField(blank=True)
    aktif           = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Workload Standard'
        verbose_name_plural = 'Workload Standards'
        ordering            = ['department', 'jabatan', 'nama_aktivitas']

    def __str__(self):
        return f'{self.jabatan.nama} — {self.nama_aktivitas}'


# ══════════════════════════════════════════════════════════════════════════════
#  FTE STANDARD — Standar kebutuhan headcount per jabatan / dept
# ══════════════════════════════════════════════════════════════════════════════

class FTEStandard(models.Model):
    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='fte_standards')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='fte_standards')
    jabatan    = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='fte_standards')

    fte_ideal       = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='FTE Ideal',
                                          help_text='Jumlah headcount ideal untuk posisi ini')
    fte_minimum     = models.DecimalField(max_digits=6, decimal_places=2, default=1,
                                          verbose_name='FTE Minimum')
    dasar_perhitungan = models.TextField(blank=True, verbose_name='Dasar Perhitungan',
                                         help_text='Asumsi / metode yang digunakan')
    tahun           = models.IntegerField(verbose_name='Tahun Referensi')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'FTE Standard'
        verbose_name_plural = 'FTE Standards'
        ordering            = ['department', 'jabatan']
        unique_together     = ['company', 'department', 'jabatan', 'tahun']

    def __str__(self):
        jabatan_str = self.jabatan.nama if self.jabatan else 'Semua Jabatan'
        return f'{self.department.nama} / {jabatan_str} — FTE {self.fte_ideal}'


# ══════════════════════════════════════════════════════════════════════════════
#  FTE PLANNING RESULT — Hasil analisis gap FTE (snapshot per periode)
# ══════════════════════════════════════════════════════════════════════════════

class FTEPlanningResult(models.Model):
    STATUS_CHOICES = [
        ('over',    'Over-staffed'),
        ('ideal',   'Ideal'),
        ('under',   'Under-staffed'),
    ]

    company         = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='fte_results')
    department      = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='fte_results')
    jabatan         = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='fte_results')
    fte_standard    = models.ForeignKey(FTEStandard, on_delete=models.SET_NULL, null=True, blank=True)

    tanggal_analisis = models.DateField(verbose_name='Tanggal Analisis', auto_now_add=True)
    headcount_aktual = models.IntegerField(verbose_name='Headcount Aktual')
    fte_ideal        = models.DecimalField(max_digits=6, decimal_places=2)
    gap              = models.DecimalField(max_digits=6, decimal_places=2,
                                           verbose_name='Gap (Aktual - Ideal)')
    status           = models.CharField(max_length=10, choices=STATUS_CHOICES)
    catatan          = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'FTE Planning Result'
        verbose_name_plural = 'FTE Planning Results'
        ordering            = ['-tanggal_analisis', 'department']

    def __str__(self):
        jabatan_str = self.jabatan.nama if self.jabatan else 'All'
        return f'{self.department.nama}/{jabatan_str} — Gap {self.gap:+.1f}'

    def save(self, *args, **kwargs):
        self.gap = float(self.headcount_aktual) - float(self.fte_ideal)
        if self.gap > 0.5:
            self.status = 'over'
        elif self.gap < -0.5:
            self.status = 'under'
        else:
            self.status = 'ideal'
        super().save(*args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
#  OD FASE 2 — COMPETENCY FRAMEWORK
# ══════════════════════════════════════════════════════════════════════════════

class CompetencyCategory(models.Model):
    """Kategori kompetensi: Technical, Behavioral, Leadership, dll."""
    company     = models.ForeignKey(Company, on_delete=models.CASCADE,
                                    related_name='competency_categories')
    nama        = models.CharField(max_length=100, verbose_name='Nama Kategori')
    deskripsi   = models.TextField(blank=True)
    warna       = models.CharField(max_length=7, default='#818cf8',
                                   verbose_name='Warna (hex)')
    urutan      = models.IntegerField(default=0)
    aktif       = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Competency Category'
        verbose_name_plural = 'Competency Categories'
        ordering            = ['urutan', 'nama']

    def __str__(self):
        return self.nama


class Competency(models.Model):
    """Definisi satu kompetensi beserta level deskriptornya."""
    LEVEL_CHOICES = [(i, f'Level {i}') for i in range(1, 6)]

    company     = models.ForeignKey(Company, on_delete=models.CASCADE,
                                    related_name='competencies')
    kategori    = models.ForeignKey(CompetencyCategory, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='competencies')
    kode        = models.CharField(max_length=20, verbose_name='Kode')
    nama        = models.CharField(max_length=150, verbose_name='Nama Kompetensi')
    deskripsi   = models.TextField(blank=True)
    # Level descriptor 1-5
    level_1_desc = models.TextField(blank=True, verbose_name='Deskripsi Level 1 (Dasar)')
    level_2_desc = models.TextField(blank=True, verbose_name='Deskripsi Level 2 (Berkembang)')
    level_3_desc = models.TextField(blank=True, verbose_name='Deskripsi Level 3 (Kompeten)')
    level_4_desc = models.TextField(blank=True, verbose_name='Deskripsi Level 4 (Mahir)')
    level_5_desc = models.TextField(blank=True, verbose_name='Deskripsi Level 5 (Ahli/Expert)')
    aktif       = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Kompetensi'
        verbose_name_plural = 'Kompetensi'
        ordering            = ['kategori', 'kode']
        unique_together     = ['company', 'kode']

    def __str__(self):
        return f'[{self.kode}] {self.nama}'

    def get_level_desc(self, level):
        return getattr(self, f'level_{level}_desc', '') or f'Level {level}'


class PositionCompetency(models.Model):
    """Standar level kompetensi yang dibutuhkan per jabatan."""
    company     = models.ForeignKey(Company, on_delete=models.CASCADE,
                                    related_name='position_competencies')
    jabatan     = models.ForeignKey(Position, on_delete=models.CASCADE,
                                    related_name='required_competencies')
    competency  = models.ForeignKey(Competency, on_delete=models.CASCADE,
                                    related_name='position_requirements')
    level_required = models.IntegerField(default=3, choices=[(i, f'Level {i}') for i in range(1, 6)],
                                         verbose_name='Level yang Dibutuhkan')
    bobot       = models.IntegerField(default=1, verbose_name='Bobot (1-5)',
                                      help_text='Kepentingan kompetensi ini untuk jabatan')
    wajib       = models.BooleanField(default=True, verbose_name='Wajib / Mandatory')

    class Meta:
        verbose_name        = 'Standar Kompetensi Jabatan'
        verbose_name_plural = 'Standar Kompetensi Jabatan'
        unique_together     = ['jabatan', 'competency']
        ordering            = ['-wajib', '-bobot']

    def __str__(self):
        return f'{self.jabatan.nama} — {self.competency.kode} L{self.level_required}'


class EmployeeCompetency(models.Model):
    """Penilaian aktual level kompetensi seorang karyawan."""
    METODE_CHOICES = [
        ('self',    'Self Assessment'),
        ('manager', 'Manager Assessment'),
        ('360',     '360° Assessment'),
        ('test',    'Uji Kompetensi'),
    ]

    company     = models.ForeignKey(Company, on_delete=models.CASCADE,
                                    related_name='employee_competencies')
    employee    = models.ForeignKey('employees.Employee', on_delete=models.CASCADE,
                                    related_name='competency_assessments')
    competency  = models.ForeignKey(Competency, on_delete=models.CASCADE,
                                    related_name='employee_assessments')
    level_aktual = models.IntegerField(default=1, choices=[(i, f'Level {i}') for i in range(1, 6)],
                                       verbose_name='Level Aktual')
    metode      = models.CharField(max_length=10, choices=METODE_CHOICES, default='manager')
    catatan     = models.TextField(blank=True)
    dinilai_oleh = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='competency_assessor',
                                     verbose_name='Dinilai Oleh')
    tanggal_penilaian = models.DateField(verbose_name='Tanggal Penilaian', auto_now_add=True)
    periode     = models.CharField(max_length=7, verbose_name='Periode (YYYY)',
                                   help_text='Contoh: 2026')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Penilaian Kompetensi Karyawan'
        verbose_name_plural = 'Penilaian Kompetensi Karyawan'
        ordering            = ['-tanggal_penilaian']
        unique_together     = ['employee', 'competency', 'periode']

    def __str__(self):
        return f'{self.employee.nama} — {self.competency.kode} L{self.level_aktual} ({self.periode})'

    @property
    def gap(self):
        """Gap = aktual - required. Negatif = perlu development."""
        req = PositionCompetency.objects.filter(
            jabatan=self.employee.jabatan, competency=self.competency
        ).first()
        if req:
            return self.level_aktual - req.level_required
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  TRAINING & DEVELOPMENT — bagian dari modul OD
# ══════════════════════════════════════════════════════════════════════════════

class TrainingProgram(models.Model):
    """Master program / agenda training yang tersedia di perusahaan."""
    KATEGORI_CHOICES = [
        ('technical',    'Technical Skill'),
        ('soft_skill',   'Soft Skill'),
        ('leadership',   'Leadership'),
        ('compliance',   'Compliance / Regulasi'),
        ('onboarding',   'Onboarding'),
        ('sertifikasi',  'Sertifikasi'),
        ('lainnya',      'Lainnya'),
    ]
    METODE_CHOICES = [
        ('offline',  'Offline / Tatap Muka'),
        ('online',   'Online / E-Learning'),
        ('hybrid',   'Hybrid'),
        ('otodidak', 'Mandiri / Otodidak'),
    ]

    company       = models.ForeignKey(Company, on_delete=models.CASCADE,
                                      related_name='training_programs')
    nama          = models.CharField(max_length=200, verbose_name='Nama Program Training')
    kategori      = models.CharField(max_length=15, choices=KATEGORI_CHOICES, default='technical')
    metode        = models.CharField(max_length=10, choices=METODE_CHOICES, default='offline')
    penyelenggara = models.CharField(max_length=200, blank=True, verbose_name='Penyelenggara / Vendor')
    deskripsi     = models.TextField(blank=True, verbose_name='Deskripsi & Tujuan')
    durasi_jam    = models.DecimalField(max_digits=6, decimal_places=1, default=8,
                                        verbose_name='Durasi (jam)')
    biaya_est     = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                        verbose_name='Estimasi Biaya (Rp)')
    kompetensi_terkait = models.ManyToManyField(
        'Competency', blank=True,
        related_name='training_programs',
        verbose_name='Kompetensi yang Ditingkatkan'
    )
    aktif       = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Program Training'
        verbose_name_plural = 'Program Training'
        ordering            = ['kategori', 'nama']

    def __str__(self):
        return f'[{self.get_kategori_display()}] {self.nama}'


class TrainingPlan(models.Model):
    """Rencana training untuk seorang karyawan pada suatu periode."""
    STATUS_CHOICES = [
        ('rencana',   'Direncanakan'),
        ('disetujui', 'Disetujui'),
        ('berjalan',  'Sedang Berjalan'),
        ('selesai',   'Selesai'),
        ('batal',     'Dibatalkan'),
    ]

    company     = models.ForeignKey(Company, on_delete=models.CASCADE,
                                    related_name='training_plans')
    employee    = models.ForeignKey('employees.Employee', on_delete=models.CASCADE,
                                    related_name='training_plans',
                                    verbose_name='Karyawan')
    program     = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE,
                                    related_name='plans',
                                    verbose_name='Program Training')
    periode         = models.CharField(max_length=7, verbose_name='Periode (YYYY)',
                                       help_text='Contoh: 2026')
    tanggal_rencana = models.DateField(verbose_name='Tanggal Rencana Pelaksanaan',
                                       null=True, blank=True)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='rencana')
    prioritas       = models.IntegerField(default=2,
                                          choices=[(1,'Tinggi'),(2,'Sedang'),(3,'Rendah')],
                                          verbose_name='Prioritas')
    alasan          = models.TextField(blank=True, verbose_name='Alasan / Kebutuhan Training')
    diusulkan_oleh  = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         related_name='training_plans_diusulkan',
                                         verbose_name='Diusulkan Oleh')
    disetujui_oleh  = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         related_name='training_plans_disetujui',
                                         verbose_name='Disetujui Oleh')
    tanggal_disetujui = models.DateField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Rencana Training'
        verbose_name_plural = 'Rencana Training'
        ordering            = ['periode', 'prioritas', 'employee__nama']

    def __str__(self):
        return f'{self.employee.nama} — {self.program.nama} ({self.periode})'


class TrainingRealization(models.Model):
    """Realisasi training — bukti karyawan sudah mengikuti training."""
    HASIL_CHOICES = [
        ('lulus',       'Lulus / Kompeten'),
        ('tidak_lulus', 'Tidak Lulus'),
        ('ikut',        'Hadir (tanpa ujian)'),
    ]

    plan             = models.OneToOneField(TrainingPlan, on_delete=models.CASCADE,
                                            related_name='realization',
                                            verbose_name='Rencana Training')
    tanggal_mulai    = models.DateField(verbose_name='Tanggal Mulai')
    tanggal_selesai  = models.DateField(verbose_name='Tanggal Selesai')
    lokasi           = models.CharField(max_length=200, blank=True, verbose_name='Lokasi / Platform')
    instruktur       = models.CharField(max_length=200, blank=True, verbose_name='Instruktur / Fasilitator')
    biaya_aktual     = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                           verbose_name='Biaya Aktual (Rp)')
    hasil            = models.CharField(max_length=12, choices=HASIL_CHOICES, default='ikut',
                                        verbose_name='Hasil Training')
    nilai            = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                           verbose_name='Nilai / Skor (jika ada)')
    nomor_sertifikat = models.CharField(max_length=100, blank=True,
                                        verbose_name='Nomor Sertifikat')
    berlaku_sampai   = models.DateField(null=True, blank=True,
                                        verbose_name='Sertifikat Berlaku Sampai')
    catatan          = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Realisasi Training'
        verbose_name_plural = 'Realisasi Training'
        ordering            = ['-tanggal_selesai']

    def __str__(self):
        return f'{self.plan.employee.nama} — {self.plan.program.nama} ({self.hasil})'

    @property
    def durasi_hari(self):
        if self.tanggal_mulai and self.tanggal_selesai:
            return (self.tanggal_selesai - self.tanggal_mulai).days + 1
        return 0

    @property
    def is_sertifikat_aktif(self):
        if not self.berlaku_sampai:
            return None
        from django.utils import timezone
        return self.berlaku_sampai >= timezone.now().date()
