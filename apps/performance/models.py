from django.db import models
from apps.core.models import Company
from apps.employees.models import Employee


# ══════════════════════════════════════════════════════════════════════════════
#  PERIODE PENILAIAN
# ══════════════════════════════════════════════════════════════════════════════

class PeriodePenilaian(models.Model):
    TIPE_CHOICES = [
        ('Bulanan',     'Bulanan'),
        ('Triwulan',    'Triwulan (Q)'),
        ('Semesteran',  'Semesteran'),
        ('Tahunan',     'Tahunan'),
    ]
    STATUS_CHOICES = [
        ('draft',   'Draft'),
        ('aktif',   'Aktif'),
        ('tutup',   'Ditutup'),
    ]

    company      = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='periode_penilaian')
    nama         = models.CharField(max_length=100, verbose_name='Nama Periode')
    tipe         = models.CharField(max_length=15, choices=TIPE_CHOICES, default='Tahunan')
    tanggal_mulai= models.DateField(verbose_name='Tanggal Mulai')
    tanggal_selesai = models.DateField(verbose_name='Tanggal Selesai')
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    deskripsi    = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Periode Penilaian'
        verbose_name_plural = 'Periode Penilaian'
        ordering            = ['-tanggal_mulai']

    def __str__(self):
        return f'{self.nama} ({self.get_tipe_display()})'

    @property
    def is_aktif(self):
        return self.status == 'aktif'


# ══════════════════════════════════════════════════════════════════════════════
#  TEMPLATE KPI (Library indikator yang bisa dipakai ulang)
# ══════════════════════════════════════════════════════════════════════════════

class KPITemplate(models.Model):
    SATUAN_CHOICES = [
        ('%',       'Persentase (%)'),
        ('angka',   'Angka'),
        ('rupiah',  'Rupiah (Rp)'),
        ('hari',    'Hari'),
        ('jam',     'Jam'),
        ('unit',    'Unit'),
        ('lainnya', 'Lainnya'),
    ]
    ARAH_CHOICES = [
        ('tinggi',  'Semakin Tinggi Semakin Baik'),
        ('rendah',  'Semakin Rendah Semakin Baik'),
    ]

    company     = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='kpi_templates')
    nama        = models.CharField(max_length=200, verbose_name='Nama Indikator')
    deskripsi   = models.TextField(blank=True, verbose_name='Deskripsi')
    satuan      = models.CharField(max_length=10, choices=SATUAN_CHOICES, default='%')
    arah        = models.CharField(max_length=10, choices=ARAH_CHOICES, default='tinggi',
                                   verbose_name='Arah Penilaian')
    kategori    = models.CharField(max_length=100, blank=True, verbose_name='Kategori/Perspektif',
                                   help_text='Misal: Keuangan, Pelanggan, Proses, SDM')
    aktif       = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Template KPI'
        verbose_name_plural = 'Template KPI'
        ordering            = ['kategori', 'nama']

    def __str__(self):
        return f'{self.nama} ({self.satuan})'


# ══════════════════════════════════════════════════════════════════════════════
#  PENILAIAN KARYAWAN (Header)
# ══════════════════════════════════════════════════════════════════════════════

class PenilaianKaryawan(models.Model):
    STATUS_CHOICES = [
        ('draft',    'Draft'),
        ('submit',   'Diajukan'),
        ('review',   'Dalam Review Atasan'),
        ('approved', 'Disetujui'),
        ('rejected', 'Dikembalikan'),
    ]

    company     = models.ForeignKey(Company,  on_delete=models.CASCADE, related_name='penilaian')
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='penilaian')
    periode     = models.ForeignKey(PeriodePenilaian, on_delete=models.CASCADE, related_name='penilaian')
    atasan      = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='penilaian_sebagai_atasan',
                                    verbose_name='Penilai / Atasan')

    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    catatan_karyawan= models.TextField(blank=True, verbose_name='Catatan Karyawan')
    catatan_atasan  = models.TextField(blank=True, verbose_name='Catatan Atasan')

    # Skor akhir (dihitung otomatis dari KPI items)
    skor_kpi        = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                          verbose_name='Skor KPI (%)')
    skor_review     = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                          verbose_name='Skor Review Atasan (%)')
    skor_akhir      = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                          verbose_name='Skor Akhir (%)')
    predikat        = models.CharField(max_length=30, blank=True, verbose_name='Predikat')

    tanggal_submit  = models.DateTimeField(null=True, blank=True)
    tanggal_approve = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Penilaian Karyawan'
        verbose_name_plural = 'Penilaian Karyawan'
        ordering            = ['-created_at']
        unique_together     = ['employee', 'periode']

    def __str__(self):
        return f'{self.employee.nama} — {self.periode.nama}'

    def hitung_skor(self):
        """Hitung ulang skor KPI dari semua item lalu simpan."""
        items = self.kpi_items.all()
        if not items:
            self.skor_kpi = 0
        else:
            total_bobot  = sum(i.bobot for i in items)
            total_weighted = sum(
                (i.pencapaian_persen * i.bobot / 100)
                for i in items if i.pencapaian_persen is not None
            )
            self.skor_kpi = round(total_weighted / total_bobot * 100, 2) if total_bobot else 0

        # Skor akhir = 70% KPI + 30% Review atasan (bisa dikonfigurasi)
        self.skor_akhir = round(self.skor_kpi * 0.7 + self.skor_review * 0.3, 2)

        # Predikat
        s = float(self.skor_akhir)
        if s >= 90:
            self.predikat = 'Istimewa'
        elif s >= 80:
            self.predikat = 'Sangat Baik'
        elif s >= 70:
            self.predikat = 'Baik'
        elif s >= 60:
            self.predikat = 'Cukup'
        else:
            self.predikat = 'Perlu Perbaikan'

        self.save(update_fields=['skor_kpi', 'skor_akhir', 'predikat'])

    @property
    def predikat_color(self):
        colors = {
            'Istimewa'       : '#22c55e',
            'Sangat Baik'    : '#3b82f6',
            'Baik'           : '#f59e0b',
            'Cukup'          : '#f97316',
            'Perlu Perbaikan': '#ef4444',
        }
        return colors.get(self.predikat, '#888')


# ══════════════════════════════════════════════════════════════════════════════
#  ITEM KPI (Detail per indikator)
# ══════════════════════════════════════════════════════════════════════════════

class KPIItem(models.Model):
    penilaian   = models.ForeignKey(PenilaianKaryawan, on_delete=models.CASCADE,
                                    related_name='kpi_items')
    template    = models.ForeignKey(KPITemplate, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='kpi_items')

    nama_kpi    = models.CharField(max_length=200, verbose_name='Nama KPI')
    satuan      = models.CharField(max_length=10, default='%')
    arah        = models.CharField(max_length=10, default='tinggi')
    bobot       = models.DecimalField(max_digits=5, decimal_places=2, default=20,
                                      verbose_name='Bobot (%)')
    target      = models.DecimalField(max_digits=15, decimal_places=2,
                                      verbose_name='Target')
    realisasi   = models.DecimalField(max_digits=15, decimal_places=2,
                                      null=True, blank=True, verbose_name='Realisasi')
    catatan     = models.TextField(blank=True)

    class Meta:
        verbose_name        = 'KPI Item'
        verbose_name_plural = 'KPI Items'
        ordering            = ['nama_kpi']

    def __str__(self):
        return f'{self.nama_kpi} — {self.penilaian}'

    @property
    def pencapaian_persen(self):
        """Hitung % pencapaian vs target, sesuai arah."""
        if self.realisasi is None or self.target == 0:
            return None
        r = float(self.realisasi)
        t = float(self.target)
        if self.arah == 'tinggi':
            return min(round(r / t * 100, 2), 120)   # cap 120%
        else:
            # Semakin rendah semakin baik
            if r == 0:
                return 120
            return min(round(t / r * 100, 2), 120)

    @property
    def skor_terbobot(self):
        p = self.pencapaian_persen
        if p is None:
            return None
        return round(p * float(self.bobot) / 100, 2)


# ══════════════════════════════════════════════════════════════════════════════
#  REVIEW ATASAN (Aspek kualitatif)
# ══════════════════════════════════════════════════════════════════════════════

class ReviewAtasan(models.Model):
    SKOR_CHOICES = [
        (1, '1 — Sangat Kurang'),
        (2, '2 — Kurang'),
        (3, '3 — Cukup'),
        (4, '4 — Baik'),
        (5, '5 — Sangat Baik'),
    ]

    penilaian   = models.ForeignKey(PenilaianKaryawan, on_delete=models.CASCADE,
                                    related_name='review_items')
    aspek       = models.CharField(max_length=100, verbose_name='Aspek Penilaian',
                                   help_text='Misal: Kedisiplinan, Komunikasi, Teamwork')
    bobot       = models.DecimalField(max_digits=5, decimal_places=2, default=20,
                                      verbose_name='Bobot (%)')
    skor        = models.IntegerField(choices=SKOR_CHOICES, null=True, blank=True)
    catatan     = models.TextField(blank=True)

    class Meta:
        verbose_name        = 'Review Atasan'
        verbose_name_plural = 'Review Atasan'

    def __str__(self):
        return f'{self.aspek} — {self.penilaian}'

    @property
    def skor_persen(self):
        if self.skor is None:
            return None
        return round(self.skor / 5 * 100, 2)


# ══════════════════════════════════════════════════════════════════════════════
#  REVIEW 360°
# ══════════════════════════════════════════════════════════════════════════════

class Review360Session(models.Model):
    """Sesi Review 360° — satu sesi per karyawan per periode."""
    STATUS_CHOICES = [
        ('draft',   'Draft'),
        ('aktif',   'Aktif — Menunggu Reviewer'),
        ('selesai', 'Selesai'),
        ('batal',   'Dibatalkan'),
    ]

    company     = models.ForeignKey(Company, on_delete=models.CASCADE,
                                    related_name='review360_sessions')
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                    related_name='review360_as_subject',
                                    verbose_name='Karyawan yang Dinilai')
    periode     = models.ForeignKey(PeriodePenilaian, on_delete=models.CASCADE,
                                    related_name='review360_sessions')
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    deadline    = models.DateField(null=True, blank=True, verbose_name='Batas Waktu Pengisian')
    skor_atasan  = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    skor_rekan   = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    skor_bawahan = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    skor_self    = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    skor_360     = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                       verbose_name='Skor 360° (Gabungan)')
    predikat     = models.CharField(max_length=30, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Sesi Review 360°'
        verbose_name_plural = 'Sesi Review 360°'
        ordering            = ['-created_at']
        unique_together     = ['employee', 'periode']

    def __str__(self):
        return f'360° {self.employee.nama} — {self.periode.nama}'

    def hitung_skor(self):
        reviews = self.reviews.filter(is_submitted=True)

        def avg(qs):
            vals = [r.skor_total for r in qs if r.skor_total is not None]
            return round(sum(vals) / len(vals), 2) if vals else None

        s_atasan  = avg(reviews.filter(tipe='atasan'))
        s_rekan   = avg(reviews.filter(tipe='rekan'))
        s_bawahan = avg(reviews.filter(tipe='bawahan'))
        s_self    = avg(reviews.filter(tipe='self'))

        bobot    = {'atasan': 0.40, 'rekan': 0.30, 'bawahan': 0.20, 'self': 0.10}
        skor_map = {'atasan': s_atasan, 'rekan': s_rekan,
                    'bawahan': s_bawahan, 'self': s_self}

        available = {k: v for k, v in skor_map.items() if v is not None}
        if not available:
            return

        total_bobot   = sum(bobot[k] for k in available)
        skor_gabungan = sum(skor_map[k] * bobot[k] / total_bobot for k in available)

        self.skor_atasan  = s_atasan  or 0
        self.skor_rekan   = s_rekan   or 0
        self.skor_bawahan = s_bawahan or 0
        self.skor_self    = s_self    or 0
        self.skor_360     = round(skor_gabungan, 2)

        s = float(self.skor_360)
        if s >= 90:   self.predikat = 'Istimewa'
        elif s >= 80: self.predikat = 'Sangat Baik'
        elif s >= 70: self.predikat = 'Baik'
        elif s >= 60: self.predikat = 'Cukup'
        else:         self.predikat = 'Perlu Perbaikan'

        self.save(update_fields=['skor_atasan','skor_rekan','skor_bawahan',
                                 'skor_self','skor_360','predikat'])


class Review360Aspek(models.Model):
    """Master aspek / pertanyaan untuk Review 360°."""
    TIPE_CHOICES = [
        ('semua',   'Semua Tipe Reviewer'),
        ('atasan',  'Hanya Atasan'),
        ('rekan',   'Rekan & Bawahan'),
        ('self',    'Hanya Self'),
    ]

    company       = models.ForeignKey(Company, on_delete=models.CASCADE,
                                      related_name='review360_aspek')
    nama          = models.CharField(max_length=200, verbose_name='Aspek / Pertanyaan')
    deskripsi     = models.TextField(blank=True, verbose_name='Panduan Penilaian')
    tipe_reviewer = models.CharField(max_length=10, choices=TIPE_CHOICES, default='semua',
                                     verbose_name='Ditampilkan ke')
    bobot         = models.DecimalField(max_digits=5, decimal_places=2, default=20,
                                        verbose_name='Bobot (%)')
    urutan        = models.IntegerField(default=0)
    aktif         = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Aspek Review 360°'
        verbose_name_plural = 'Aspek Review 360°'
        ordering            = ['urutan', 'nama']

    def __str__(self):
        return self.nama


class Review360Reviewer(models.Model):
    """Satu reviewer dalam sesi 360°."""
    TIPE_CHOICES = [
        ('self',    'Self-Assessment'),
        ('atasan',  'Atasan'),
        ('rekan',   'Rekan Sejawat'),
        ('bawahan', 'Bawahan'),
    ]

    session        = models.ForeignKey(Review360Session, on_delete=models.CASCADE,
                                       related_name='reviews')
    reviewer       = models.ForeignKey(Employee, on_delete=models.CASCADE,
                                       related_name='review360_as_reviewer',
                                       verbose_name='Reviewer')
    tipe           = models.CharField(max_length=10, choices=TIPE_CHOICES,
                                      verbose_name='Tipe Hubungan')
    is_submitted   = models.BooleanField(default=False, verbose_name='Sudah Diisi')
    tanggal_submit = models.DateTimeField(null=True, blank=True)
    catatan_umum   = models.TextField(blank=True, verbose_name='Catatan / Feedback Umum')
    skor_total     = models.DecimalField(max_digits=5, decimal_places=2,
                                         null=True, blank=True,
                                         verbose_name='Skor Total (%)')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Reviewer 360°'
        verbose_name_plural = 'Reviewer 360°'
        unique_together     = ['session', 'reviewer']
        ordering            = ['tipe', 'reviewer__nama']

    def __str__(self):
        return f'{self.reviewer.nama} ({self.get_tipe_display()}) → {self.session.employee.nama}'

    def hitung_skor(self):
        items = self.answer_items.all()
        if not items:
            return
        vals = [i.skor_persen for i in items if i.skor_persen is not None]
        self.skor_total = round(sum(vals) / len(vals), 2) if vals else None
        self.save(update_fields=['skor_total'])


class Review360AnswerItem(models.Model):
    """Jawaban satu aspek oleh satu reviewer."""
    SKOR_CHOICES = [
        (1, '1 — Sangat Kurang'),
        (2, '2 — Kurang'),
        (3, '3 — Cukup'),
        (4, '4 — Baik'),
        (5, '5 — Sangat Baik'),
    ]

    reviewer = models.ForeignKey(Review360Reviewer, on_delete=models.CASCADE,
                                  related_name='answer_items')
    aspek    = models.ForeignKey(Review360Aspek, on_delete=models.CASCADE,
                                  related_name='answers')
    skor     = models.IntegerField(choices=SKOR_CHOICES, null=True, blank=True)
    catatan  = models.TextField(blank=True)

    class Meta:
        verbose_name        = 'Jawaban Review 360°'
        verbose_name_plural = 'Jawaban Review 360°'
        unique_together     = ['reviewer', 'aspek']

    def __str__(self):
        return f'{self.reviewer} — {self.aspek.nama}: {self.skor}'

    @property
    def skor_persen(self):
        if self.skor is None:
            return None
        return round(self.skor / 5 * 100, 2)
