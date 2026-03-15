"""
apps/advanced_psychotest/models.py

Add-On: Advanced Psychometric Test Suite
Berisi 5 jenis tes untuk proses recruitment:
  1. Raven's Progressive Matrices  → fluid intelligence, non-verbal
  2. Cognitive Speed Test           → inspired by Wonderlic, 50 soal / 12 menit
  3. Big Five (OCEAN)               → kepribadian 5 dimensi
  4. Situational Judgement Test     → penilaian situasi kerja nyata
  5. Culture Fair Intelligence Test → intelegensi tanpa bias budaya
"""
import uuid
from django.db import models
from apps.core.models import Company
from django.utils import timezone
from datetime import timedelta


# ─────────────────────────────────────────────────────────────────────────────
# KONSTANTA TIPE TES
# ─────────────────────────────────────────────────────────────────────────────

TEST_TYPE_CHOICES = [
    ('raven',   "Raven's Progressive Matrices"),
    ('cogspeed', 'Cognitive Speed Test'),
    ('bigfive',  'Big Five Personality (OCEAN)'),
    ('sjt',      'Situational Judgement Test'),
    ('cfit',     'Culture Fair Intelligence Test'),
]

# Durasi default (menit) per tipe
TEST_DURATION = {
    'raven':    25,
    'cogspeed': 12,
    'bigfive':  20,
    'sjt':      30,
    'cfit':     20,
}

# ─────────────────────────────────────────────────────────────────────────────
# SOAL BANK — ADVANCED
# ─────────────────────────────────────────────────────────────────────────────

class AdvSoal(models.Model):
    """Bank soal untuk semua tipe tes advanced."""

    TIPE_SOAL_CHOICES = [
        ('pilihan_ganda',  'Pilihan Ganda (satu jawaban benar)'),
        ('likert',         'Likert Scale 1-5 (Big Five)'),
        ('sjt_rank',       'SJT Ranking (urutkan respons)'),
        ('best_worst',     'Best / Worst (pilih terbaik & terburuk)'),
    ]

    test_type   = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)
    tipe_soal   = models.CharField(max_length=20, choices=TIPE_SOAL_CHOICES,
                                    default='pilihan_ganda')
    nomor       = models.IntegerField(default=1, verbose_name='Nomor Soal')

    # Pertanyaan / stem
    pertanyaan  = models.TextField(verbose_name='Pertanyaan / Deskripsi Situasi')

    # Untuk pilihan ganda & SJT: opsi A-D
    opsi_a      = models.TextField(blank=True, verbose_name='Opsi A')
    opsi_b      = models.TextField(blank=True, verbose_name='Opsi B')
    opsi_c      = models.TextField(blank=True, verbose_name='Opsi C')
    opsi_d      = models.TextField(blank=True, verbose_name='Opsi D')
    opsi_e      = models.TextField(blank=True, verbose_name='Opsi E (Likert ke-5)')
    jawaban_benar = models.CharField(max_length=1, blank=True,
                                      help_text='A/B/C/D — kosong untuk likert/sjt_rank')

    # Big Five: dimensi yang diukur oleh soal ini
    BIGFIVE_DIM = [
        ('O', 'Openness'),
        ('C', 'Conscientiousness'),
        ('E', 'Extraversion'),
        ('A', 'Agreeableness'),
        ('N', 'Neuroticism'),
    ]
    bigfive_dimensi = models.CharField(max_length=1, blank=True, choices=BIGFIVE_DIM,
                                        help_text='Khusus Big Five')
    bigfive_reverse = models.BooleanField(default=False,
                                           help_text='Reverse-scored item')

    # SJT: skor per opsi (0-3 tiap opsi)
    sjt_skor_a  = models.IntegerField(default=0)
    sjt_skor_b  = models.IntegerField(default=0)
    sjt_skor_c  = models.IntegerField(default=0)
    sjt_skor_d  = models.IntegerField(default=0)

    # Metadata
    tingkat_kesulitan = models.CharField(
        max_length=10,
        choices=[('mudah','Mudah'),('sedang','Sedang'),('sulit','Sulit')],
        default='sedang'
    )
    aktif       = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Soal Advanced'
        verbose_name_plural = 'Bank Soal Advanced'
        ordering = ['test_type', 'nomor']

    def __str__(self):
        return f"[{self.get_test_type_display()}] #{self.nomor} — {self.pertanyaan[:60]}"

    @property
    def opsi_list(self):
        return [(k, getattr(self, f'opsi_{k.lower()}'))
                for k in ['A','B','C','D','E']
                if getattr(self, f'opsi_{k.lower()}', '')]


# ─────────────────────────────────────────────────────────────────────────────
# SESI TES ADVANCED
# ─────────────────────────────────────────────────────────────────────────────

def default_expired_adv():
    return timezone.now() + timedelta(days=7)


class AdvSession(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Belum Dikerjakan'),
        ('started',   'Sedang Dikerjakan'),
        ('completed', 'Selesai'),
        ('expired',   'Kadaluarsa'),
    ]

    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='adv_sessions', verbose_name='Perusahaan', null=True, blank=True)
    candidate   = models.ForeignKey(
        'recruitment.Candidate',
        on_delete=models.CASCADE,
        related_name='adv_sessions',
        null=True, blank=True,
    )
    # Untuk psikotes berkala karyawan (nullable — salah satu dari candidate/employee harus diisi)
    employee    = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='adv_sessions',
        null=True, blank=True,
    )
    # Label tujuan sesi: 'recruitment' | 'berkala' | 'promosi' | 'evaluasi'
    tujuan      = models.CharField(max_length=20, default='recruitment', blank=True)

    # paket = list tipe tes yang harus dikerjakan, e.g. ["raven","bigfive","sjt"]
    paket       = models.JSONField(
        default=list,
        help_text='List tipe tes dalam sesi ini, e.g. ["raven","cogspeed"]'
    )
    # test_type diisi otomatis dari paket[0] — dipertahankan untuk backward-compat
    test_type   = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES, blank=True)
    token       = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Durasi per tipe tes (menit) — dict, e.g. {"raven":25,"bigfive":20}
    durasi_per_tes = models.JSONField(default=dict, blank=True)
    # Tetap ada untuk backward-compat sesi lama (single tes)
    durasi_menit = models.IntegerField(default=25, verbose_name='Durasi (menit)')

    # Waktu mulai aktual per tipe — untuk timer akurat saat kandidat kembali ke halaman
    # e.g. {"raven": "2025-01-01T10:00:00Z", "bigfive": "2025-01-01T10:26:00Z"}
    tipe_started_at = models.JSONField(default=dict, blank=True)

    expired_at  = models.DateTimeField(default=default_expired_adv)
    started_at  = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by  = models.CharField(max_length=100, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sesi Advanced Test'
        verbose_name_plural = 'Sesi Advanced Test'
        ordering = ['-created_at']

    def __str__(self):
        label   = ', '.join(self.paket) if self.paket else self.test_type
        peserta = self.get_peserta_nama()
        return f"{label} — {peserta} ({self.get_status_display()})"

    @property
    def is_expired(self):
        return timezone.now() > self.expired_at

    @property
    def is_accessible(self):
        return self.status in ('pending', 'started') and not self.is_expired

    @property
    def link(self):
        return f"/advanced-test/tes/{self.token}/"

    def get_peserta(self):
        """Return candidate atau employee — siapapun yang mengerjakan tes ini."""
        return self.candidate or self.employee

    def get_peserta_nama(self):
        p = self.get_peserta()
        return p.nama if p else '-'

    def get_peserta_url(self):
        if self.candidate:
            return f'/recruitment/candidates/{self.candidate.pk}/'
        if self.employee:
            return f'/employees/{self.employee.pk}/'
        return '#'

    def get_paket(self):
        """Return list tipe tes — support sesi lama (single test_type)."""
        if self.paket:
            return list(self.paket)
        if self.test_type:
            return [self.test_type]
        return []

    def get_durasi(self, tipe):
        """Durasi menit untuk tipe tertentu."""
        if self.durasi_per_tes and tipe in self.durasi_per_tes:
            return self.durasi_per_tes[tipe]
        return TEST_DURATION.get(tipe, self.durasi_menit)

    def catat_tipe_started(self, tipe):
        """Catat waktu mulai aktual satu tipe tes (dipanggil pertama kali tes tipe itu dibuka)."""
        if tipe not in (self.tipe_started_at or {}):
            data = dict(self.tipe_started_at or {})
            data[tipe] = timezone.now().isoformat()
            self.tipe_started_at = data
            self.save(update_fields=['tipe_started_at'])

    def get_sisa_detik(self, tipe):
        """Hitung sisa detik untuk tipe tes tertentu berdasarkan waktu mulai aktual."""
        from datetime import timedelta
        started_map = self.tipe_started_at or {}
        if tipe in started_map:
            import datetime
            tipe_start = datetime.datetime.fromisoformat(started_map[tipe])
            if timezone.is_naive(tipe_start):
                tipe_start = timezone.make_aware(tipe_start)
        elif self.started_at:
            # Fallback: gunakan started_at + offset seperti sebelumnya
            paket = self.get_paket()
            tes_selesai = self.get_tes_selesai()
            offset_menit = 0
            for t in paket:
                if t == tipe:
                    break
                if t in tes_selesai:
                    offset_menit += self.get_durasi(t)
            tipe_start = self.started_at + timedelta(minutes=offset_menit)
        else:
            return None

        deadline = tipe_start + timedelta(minutes=self.get_durasi(tipe))
        sisa = deadline - timezone.now()
        return max(0, int(sisa.total_seconds()))

    def get_tes_selesai(self):
        """Return set tipe tes yang sudah selesai (semua soalnya sudah dijawab)."""
        selesai = set()
        for tipe in self.get_paket():
            total = AdvSoal.objects.filter(test_type=tipe, aktif=True).count()
            if total == 0:
                continue
            dijawab = self.answers.filter(soal__test_type=tipe).count()
            if dijawab >= total:
                selesai.add(tipe)
        return selesai

    def semua_selesai(self):
        return set(self.get_paket()) == self.get_tes_selesai()


# ─────────────────────────────────────────────────────────────────────────────
# JAWABAN KANDIDAT
# ─────────────────────────────────────────────────────────────────────────────

class AdvAnswer(models.Model):
    session     = models.ForeignKey(AdvSession, on_delete=models.CASCADE,
                                    related_name='answers')
    soal        = models.ForeignKey(AdvSoal, on_delete=models.CASCADE)
    jawaban     = models.CharField(max_length=1, blank=True,
                                   help_text='A/B/C/D untuk PG; 1-5 untuk Likert')
    # SJT ranking: urutan 4 opsi dipisah koma, e.g. "B,A,D,C"
    sjt_ranking = models.CharField(max_length=20, blank=True)
    # Likert score (sudah di-reverse jika perlu)
    likert_val  = models.IntegerField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('session', 'soal')

    @property
    def is_correct(self):
        if self.soal.tipe_soal == 'pilihan_ganda' and self.soal.jawaban_benar:
            return self.jawaban == self.soal.jawaban_benar
        return None


# ─────────────────────────────────────────────────────────────────────────────
# HASIL TES ADVANCED
# ─────────────────────────────────────────────────────────────────────────────

class AdvResult(models.Model):
    session     = models.ForeignKey(AdvSession, on_delete=models.CASCADE,
                                    related_name='results')
    candidate   = models.ForeignKey(
        'recruitment.Candidate',
        on_delete=models.CASCADE,
        related_name='adv_results',
        null=True, blank=True,
    )
    # Untuk sesi karyawan (psikotes berkala)
    employee    = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='adv_results',
        null=True, blank=True,
    )
    test_type   = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)

    # Skor utama (0-100)
    skor_total  = models.IntegerField(null=True, blank=True)
    percentile  = models.IntegerField(null=True, blank=True,
                                       help_text='Percentile vs norma populasi (estimasi)')
    grade       = models.CharField(max_length=2, blank=True)

    # Big Five — skor per dimensi (0-100)
    ocean_o     = models.IntegerField(null=True, blank=True, verbose_name='Openness')
    ocean_c     = models.IntegerField(null=True, blank=True, verbose_name='Conscientiousness')
    ocean_e     = models.IntegerField(null=True, blank=True, verbose_name='Extraversion')
    ocean_a     = models.IntegerField(null=True, blank=True, verbose_name='Agreeableness')
    ocean_n     = models.IntegerField(null=True, blank=True, verbose_name='Neuroticism')

    # Detail JSON: bisa simpan breakdown per soal atau sub-dimensi
    detail      = models.JSONField(default=dict)

    # Interpretasi otomatis
    interpretasi = models.TextField(blank=True)
    catatan_hr  = models.TextField(blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hasil Advanced Test'
        verbose_name_plural = 'Hasil Advanced Test'
        ordering = ['-created_at']
        unique_together = ('session', 'test_type')

    def __str__(self):
        peserta = (self.candidate.nama if self.candidate else
                   self.employee.nama if self.employee else '-')
        return f"Hasil {self.get_test_type_display()} — {peserta} — {self.skor_total}"

    def compute_grade(self):
        s = self.skor_total or 0
        if s >= 85: return 'A'
        if s >= 70: return 'B'
        if s >= 55: return 'C'
        if s >= 40: return 'D'
        return 'E'

    def get_ocean_summary(self):
        return {
            'Openness':          self.ocean_o,
            'Conscientiousness': self.ocean_c,
            'Extraversion':      self.ocean_e,
            'Agreeableness':     self.ocean_a,
            'Neuroticism':       self.ocean_n,
        }
