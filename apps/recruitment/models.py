from django.db import models
from apps.core.models import Company, Department, Position


class ManpowerRequest(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'), ('Approved', 'Disetujui'), ('Open', 'Dibuka'),
        ('In Process', 'Dalam Proses'), ('Filled', 'Terpenuhi'), ('Cancelled', 'Dibatalkan'),
    ]
    TIPE_CHOICES = [
        ('New Hire', 'Karyawan Baru'), ('Replacement', 'Pengganti'), ('Additional', 'Tambahan'),
    ]
    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='mprfs', verbose_name='Perusahaan')
    nomor_mprf       = models.CharField(max_length=50, unique=True, verbose_name='No. MPRF')
    department       = models.ForeignKey(Department, on_delete=models.CASCADE)
    jabatan          = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    nama_jabatan     = models.CharField(max_length=100, verbose_name='Nama Jabatan')
    tipe             = models.CharField(max_length=20, choices=TIPE_CHOICES, default='New Hire')
    jumlah_kebutuhan = models.IntegerField(default=1, verbose_name='Jumlah Kebutuhan')
    alasan           = models.TextField(verbose_name='Alasan Kebutuhan')
    kualifikasi      = models.TextField(blank=True, verbose_name='Kualifikasi')
    target_date      = models.DateField(verbose_name='Target Pengisian')
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    approved_by      = models.CharField(max_length=100, blank=True)
    approved_date    = models.DateField(null=True, blank=True)
    created_by       = models.CharField(max_length=100, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Manpower Request'
        verbose_name_plural = 'Manpower Request'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nomor_mprf} - {self.nama_jabatan}"

    @property
    def hired_count(self):
        """Jumlah kandidat yang sudah Hired untuk MPRF ini."""
        return self.candidates.filter(status='Hired').count()

    @property
    def is_fulfilled(self):
        """True jika hired sudah memenuhi atau melebihi kebutuhan."""
        return self.hired_count >= self.jumlah_kebutuhan

    @property
    def sisa_kebutuhan(self):
        """Sisa kebutuhan yang belum terpenuhi."""
        return max(0, self.jumlah_kebutuhan - self.hired_count)

    def save(self, *args, **kwargs):
        from django.db import IntegrityError
        from datetime import datetime
        if not self.nomor_mprf:
            now = datetime.now()
            count = ManpowerRequest.objects.filter(nomor_mprf__startswith=f"MPRF/{now.year}").count()
            self.nomor_mprf = f"MPRF/{now.year}{now.month:02d}/{count + 1:04d}"
        for attempt in range(5):
            try:
                super().save(*args, **kwargs)
                return
            except IntegrityError:
                if attempt < 4:
                    now = datetime.now()
                    count = ManpowerRequest.objects.filter(nomor_mprf__startswith=f"MPRF/{now.year}").count()
                    self.nomor_mprf = f"MPRF/{now.year}{now.month:02d}/{count + 1:04d}"
                else:
                    raise


class Candidate(models.Model):
    STATUS_CHOICES = [
        ('Screening', 'Screening CV'), ('Psikotes', 'Psikotes'),
        ('Interview HR', 'Interview HR'), ('Interview User', 'Interview User'),
        ('Medical Check', 'Medical Check Up'), ('Offering', 'Offering Letter'),
        ('Hired', 'Diterima'), ('Rejected', 'Ditolak'), ('Withdrawn', 'Mundur'),
    ]

    mprf             = models.ForeignKey(ManpowerRequest, on_delete=models.CASCADE,
                                         related_name='candidates', null=True, blank=True)
    nama             = models.CharField(max_length=200, verbose_name='Nama Kandidat')
    email            = models.EmailField(blank=True)
    no_hp            = models.CharField(max_length=20, blank=True)
    jabatan_dilamar  = models.CharField(max_length=100, verbose_name='Jabatan Dilamar')
    sumber           = models.CharField(max_length=50, blank=True, verbose_name='Sumber Rekrutmen')
    tanggal_melamar  = models.DateField(auto_now_add=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Screening')
    pendidikan       = models.CharField(max_length=10, blank=True)
    pengalaman_tahun = models.IntegerField(default=0, verbose_name='Pengalaman (tahun)')
    ekspektasi_gaji  = models.BigIntegerField(null=True, blank=True, verbose_name='Ekspektasi Gaji')
    cv_file          = models.FileField(upload_to='cv/', null=True, blank=True, verbose_name='File CV')
    catatan          = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    ats_score        = models.IntegerField(null=True, blank=True, verbose_name='Skor ATS')
    ats_grade        = models.CharField(max_length=2, blank=True, verbose_name='Grade ATS')
    ats_rekomendasi  = models.CharField(max_length=20, blank=True)
    ats_detail       = models.JSONField(null=True, blank=True, verbose_name='Detail ATS')
    psikotes_score   = models.IntegerField(null=True, blank=True, verbose_name='Skor Psikotes')
    psikotes_grade   = models.CharField(max_length=2, blank=True)
    psikotes_detail  = models.JSONField(null=True, blank=True)
    interview_score  = models.IntegerField(null=True, blank=True, verbose_name='Skor Interview')

    class Meta:
        verbose_name = 'Kandidat'
        verbose_name_plural = 'Kandidat'
        ordering = ['-tanggal_melamar']

    def __str__(self):
        return f"{self.nama} - {self.jabatan_dilamar}"

    @property
    def total_score(self):
        scores = []
        if self.ats_score is not None:      scores.append(self.ats_score)
        if self.psikotes_score is not None: scores.append(self.psikotes_score)
        if self.interview_score is not None: scores.append(self.interview_score)
        return round(sum(scores) / len(scores)) if scores else None

    @property
    def total_grade(self):
        s = self.total_score
        if s is None: return '-'
        if s >= 80:   return 'A'
        if s >= 65:   return 'B'
        if s >= 50:   return 'C'
        return 'D'

    @property
    def total_rekomendasi(self):
        s = self.total_score
        if s is None: return '-'
        if s >= 80:   return 'Lanjutkan'
        if s >= 50:   return 'Pertimbangkan'
        return 'Tolak'

    @property
    def rekomendasi_color(self):
        r = self.total_rekomendasi
        if r == 'Lanjutkan':      return 'success'
        if r == 'Pertimbangkan':  return 'warning'
        if r == 'Tolak':          return 'danger'
        return 'secondary'

    @property
    def active_modules(self):
        mods = []
        if self.ats_score is not None:
            mods.append({'nama': 'ATS CV', 'score': self.ats_score,
                         'grade': self.ats_grade, 'icon': 'fa-file-alt'})
        if self.psikotes_score is not None:
            mods.append({'nama': 'Psikotes', 'score': self.psikotes_score,
                         'grade': self.psikotes_grade, 'icon': 'fa-brain'})
        if self.interview_score is not None:
            mods.append({'nama': 'Interview', 'score': self.interview_score,
                         'grade': '', 'icon': 'fa-comments'})
        return mods


# ── Company Setting (singleton) ────────────────────────────────────────────────
class CompanySetting(models.Model):
    nama_perusahaan = models.CharField(max_length=200, default='PT. Nama Perusahaan',
                                        verbose_name='Nama Perusahaan')
    logo            = models.ImageField(upload_to='company/', null=True, blank=True,
                                        verbose_name='Logo Perusahaan')
    hrd_manager     = models.CharField(max_length=100, blank=True, default='HRD Manager',
                                        verbose_name='Nama HRD Manager')
    format_nomor_ol = models.CharField(
        max_length=100, default='OL/{YYYY}{MM}/{SEQ:04d}',
        verbose_name='Format Nomor OL',
        help_text='Variabel: {YYYY}=tahun, {YY}=2digit tahun, {MM}=bulan, {DD}=hari, {SEQ}=urutan. '
                  'Contoh: OL/{YYYY}/{MM}/{SEQ:04d} → OL/2025/06/0001')
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Company Setting'
        verbose_name_plural = 'Company Settings'

    def __str__(self):
        return self.nama_perusahaan

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def generate_nomor_ol(self):
        """Generate nomor OL berdasarkan format yang dikonfigurasi."""
        from datetime import datetime
        now = datetime.now()
        # Hitung SEQ: berapa OL yang sudah ada bulan ini
        prefix_check = self.format_nomor_ol.split('{SEQ')[0]
        prefix_check = prefix_check.replace('{YYYY}', str(now.year))
        prefix_check = prefix_check.replace('{YY}', str(now.year)[-2:])
        prefix_check = prefix_check.replace('{MM}', f'{now.month:02d}')
        prefix_check = prefix_check.replace('{DD}', f'{now.day:02d}')
        count = OfferingLetter.objects.filter(nomor__startswith=prefix_check).count()
        seq = count + 1

        nomor = self.format_nomor_ol
        nomor = nomor.replace('{YYYY}', str(now.year))
        nomor = nomor.replace('{YY}', str(now.year)[-2:])
        nomor = nomor.replace('{MM}', f'{now.month:02d}')
        nomor = nomor.replace('{DD}', f'{now.day:02d}')
        # Handle {SEQ:04d} or {SEQ}
        import re
        nomor = re.sub(r'\{SEQ:(\d+)d\}', lambda m: f'{seq:0{m.group(1)}d}', nomor)
        nomor = nomor.replace('{SEQ}', str(seq))
        return nomor


# ── Offering Template ──────────────────────────────────────────────────────────
class OfferingTemplate(models.Model):
    nama                    = models.CharField(max_length=100, verbose_name='Nama Template')
    deskripsi               = models.TextField(blank=True, verbose_name='Deskripsi')
    is_default              = models.BooleanField(default=False, verbose_name='Jadikan Default')
    working_day_text        = models.TextField(
        default='Roster Working Day, every day working including National Holiday/Red Calendar day, '
                'able to take Rest one day after two weeks work at Site, 07.30 – 16.00 '
                '(base on field working time)',
        verbose_name='Working Day')
    employment_status_text  = models.TextField(
        default='First Contract (PKWT I) : 6 (Six) months, If your evaluation is good/excellent, '
                'company will be consider to extend your working agreement to (PKWT II)',
        verbose_name='Employment Status')
    meal_allowance_text     = models.CharField(
        max_length=300, default='Provided by Company (breakfast, lunch, & dinner)',
        verbose_name='Meal Allowance')
    residence_allowance_text = models.CharField(
        max_length=300, default='Provided by Company (mess/dormitory)',
        verbose_name='Residence Allowance')
    roster_leave_text       = models.CharField(
        max_length=100, default='10 : 2 (working 10 weeks)', verbose_name='Roster Leave')
    annual_leave_text       = models.CharField(
        max_length=300, default='12 months work continually, 12 working days Leave',
        verbose_name='Annual Leave')
    overtime_text           = models.CharField(
        max_length=300, default='Job Position Assignment Responsibility',
        verbose_name='Overtime Policy')
    bpjs_kes_text           = models.CharField(
        max_length=300, default='Health Care (Employee dues obligation by regulation)',
        verbose_name='BPJS Kesehatan')
    bpjs_tk_text            = models.CharField(
        max_length=300, default='JHT,JKK,JK,JP (JHT&JP; Employee dues obligation by regulation)',
        verbose_name='BPJS Ketenagakerjaan')
    bpjs_potongan_text      = models.CharField(
        max_length=300, default='Deducted 2% JHT, 1% JP, 1% Kes From Salary for BPJS TK & Kes.',
        verbose_name='Potongan BPJS')
    pph21_text              = models.CharField(
        max_length=300, default='Income Tax is covered by Company', verbose_name='PPh 21')
    footer_text             = models.TextField(
        default='The mentioned statement above as our agreement previous, so please sign the letter '
                'and submit the letter back to us as your acceptance to the term & condition in the '
                'agreement as soon as possible.\n\nThanks you for your attention and cooperation.',
        verbose_name='Footer Text')
    created_at              = models.DateTimeField(auto_now_add=True)
    updated_at              = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Offering Template'
        verbose_name_plural = 'Offering Templates'
        ordering = ['-is_default', 'nama']

    def __str__(self):
        return f"{self.nama}{'  ★ Default' if self.is_default else ''}"

    def save(self, *args, **kwargs):
        # Hanya satu template yang bisa jadi default
        if self.is_default:
            OfferingTemplate.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ── Offering Letter ────────────────────────────────────────────────────────────
class OfferingLetter(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'), ('Sent', 'Dikirim'), ('Accepted', 'Diterima'),
        ('Rejected', 'Ditolak'), ('Expired', 'Kadaluarsa'),
    ]
    nomor               = models.CharField(max_length=50, unique=True, verbose_name='Nomor Surat')
    candidate           = models.ForeignKey(Candidate, on_delete=models.CASCADE,
                                             related_name='offering_letters')
    template            = models.ForeignKey(OfferingTemplate, on_delete=models.SET_NULL,
                                             null=True, blank=True, verbose_name='Template')
    jabatan             = models.CharField(max_length=100)
    department          = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    tanggal_surat       = models.DateField(verbose_name='Tanggal Surat')
    tanggal_mulai_kerja = models.DateField(verbose_name='Tanggal Mulai Kerja')
    site_lokasi         = models.CharField(max_length=200, blank=True, default='',
                                            verbose_name='Site/Lokasi Surat')
    lokasi_kerja        = models.CharField(max_length=300, blank=True, default='',
                                            verbose_name='Lokasi Kerja')
    point_of_hire       = models.CharField(max_length=100, blank=True, default='',
                                            verbose_name='Point of Hire (POH)')
    join_date_text      = models.CharField(max_length=100, blank=True, default='As Soon As Possible',
                                            verbose_name='Expected Join Date')
    gaji_pokok          = models.BigIntegerField(verbose_name='Gaji Pokok')
    fixed_allowance     = models.BigIntegerField(default=0, verbose_name='Fixed Allowance')
    tunjangan_total     = models.BigIntegerField(default=0, verbose_name='Total Tunjangan Lain')
    STATUS_KARYAWAN_CHOICES = [
        ('PKWT',  'PKWT (Kontrak)'),
        ('PKWTT', 'PKWTT (Permanen)'),
        ('PHL',   'PHL (Harian Lepas)'),
    ]
    status_karyawan     = models.CharField(max_length=10, choices=STATUS_KARYAWAN_CHOICES,
                                            default='PKWT', verbose_name='Status Karyawan')
    jangka_waktu        = models.CharField(max_length=100, blank=True, default='',
                                            verbose_name='Jangka Waktu Perjanjian')
    masa_probasi        = models.IntegerField(default=3, verbose_name='Masa Probasi (bulan)')
    no_arsip            = models.CharField(max_length=100, blank=True, default='',
                                            verbose_name='No. Arsip')
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    keterangan          = models.TextField(blank=True)
    file_pdf            = models.FileField(upload_to='offering_letters/', null=True, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Offering Letter'
        verbose_name_plural = 'Offering Letter'
        ordering = ['-tanggal_surat']

    def __str__(self):
        return f"{self.nomor} - {self.candidate.nama}"

    def save(self, *args, **kwargs):
        from django.db import IntegrityError
        if not self.nomor:
            setting = CompanySetting.get()
            self.nomor = setting.generate_nomor_ol()
        for attempt in range(5):
            try:
                super().save(*args, **kwargs)
                return
            except IntegrityError:
                if attempt < 4:
                    setting = CompanySetting.get()
                    self.nomor = setting.generate_nomor_ol()
                else:
                    raise

    def format_gaji(self, val):
        return f"Rp. {val:,.0f},-".replace(',', '.')

    @property
    def gaji_pokok_str(self):
        return self.format_gaji(self.gaji_pokok)

    @property
    def fixed_allowance_str(self):
        return self.format_gaji(self.fixed_allowance)
