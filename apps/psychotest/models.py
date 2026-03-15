"""
apps/psychotest/models.py

Model untuk modul Psikotes:
  - SoalBank      : Bank soal (Logika / Verbal / Numerik / DISC)
  - PsikotesSession: Sesi tes per kandidat (punya token unik + expired)
  - PsikotesAnswer : Jawaban per soal dari kandidat
  - PsikotesResult : Hasil akhir perhitungan skor + profil DISC
"""

import uuid
from django.db import models
from apps.core.models import Company
from django.utils import timezone
from datetime import timedelta


# ─────────────────────────────────────────────────────────────────────────────
# SOAL BANK
# ─────────────────────────────────────────────────────────────────────────────

class SoalBank(models.Model):
    KATEGORI_CHOICES = [
        ('logika',  'Logika'),
        ('verbal',  'Verbal'),
        ('numerik', 'Numerik'),
        ('disc',    'DISC Personality'),
    ]
    TIPE_CHOICES = [
        ('pilihan_ganda', 'Pilihan Ganda'),
        ('disc_set',      'DISC Set (pilih paling/kurang)'),
    ]

    kategori    = models.CharField(max_length=20, choices=KATEGORI_CHOICES)
    tipe        = models.CharField(max_length=20, choices=TIPE_CHOICES, default='pilihan_ganda')
    pertanyaan  = models.TextField(verbose_name='Pertanyaan / Soal')
    # Untuk pilihan_ganda: opsi A-D disimpan di sini
    opsi_a      = models.CharField(max_length=300, blank=True, verbose_name='Opsi A')
    opsi_b      = models.CharField(max_length=300, blank=True, verbose_name='Opsi B')
    opsi_c      = models.CharField(max_length=300, blank=True, verbose_name='Opsi C')
    opsi_d      = models.CharField(max_length=300, blank=True, verbose_name='Opsi D')
    jawaban_benar = models.CharField(max_length=1, blank=True,
                                     help_text='A/B/C/D — kosongkan untuk soal DISC')
    # Untuk DISC: setiap opsi punya dimensi D/I/S/C
    disc_a      = models.CharField(max_length=1, blank=True, help_text='D/I/S/C')
    disc_b      = models.CharField(max_length=1, blank=True)
    disc_c      = models.CharField(max_length=1, blank=True)
    disc_d      = models.CharField(max_length=1, blank=True)

    urutan      = models.IntegerField(default=0, verbose_name='Urutan tampil')
    aktif       = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Soal Bank'
        verbose_name_plural = 'Soal Bank'
        ordering = ['kategori', 'urutan', 'id']

    def __str__(self):
        return f"[{self.get_kategori_display()}] {self.pertanyaan[:60]}"

    @property
    def opsi_list(self):
        """Return list of (key, text) untuk render template."""
        opts = []
        for k in ['A', 'B', 'C', 'D']:
            txt = getattr(self, f'opsi_{k.lower()}', '')
            if txt:
                opts.append((k, txt))
        return opts


# ─────────────────────────────────────────────────────────────────────────────
# SESI PSIKOTES
# ─────────────────────────────────────────────────────────────────────────────

def default_expired():
    return timezone.now() + timedelta(days=7)


class PsikotesSession(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Belum Dikerjakan'),
        ('started',   'Sedang Dikerjakan'),
        ('completed', 'Selesai'),
        ('expired',   'Kadaluarsa'),
    ]

    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='psychotest_sessions', verbose_name='Perusahaan', null=True, blank=True)
    candidate   = models.ForeignKey(
        'recruitment.Candidate',
        on_delete=models.CASCADE,
        related_name='psychotest_sessions'
    )
    token       = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    paket       = models.JSONField(
        default=list,
        help_text='List kategori yang diujikan, e.g. ["logika","verbal","numerik","disc"]'
    )
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expired_at  = models.DateTimeField(default=default_expired)
    started_at  = models.DateTimeField(null=True, blank=True)
    completed_at= models.DateTimeField(null=True, blank=True)
    created_by  = models.CharField(max_length=100, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    # Durasi per kategori (menit) — bisa dikustom saat buat sesi
    durasi_logika   = models.IntegerField(default=15)
    durasi_verbal   = models.IntegerField(default=15)
    durasi_numerik  = models.IntegerField(default=15)
    durasi_disc     = models.IntegerField(default=20)

    class Meta:
        verbose_name = 'Sesi Psikotes'
        verbose_name_plural = 'Sesi Psikotes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Psikotes — {self.candidate.nama} ({self.get_status_display()})"

    @property
    def is_expired(self):
        return timezone.now() > self.expired_at

    @property
    def is_accessible(self):
        return self.status in ('pending', 'started') and not self.is_expired

    @property
    def link(self):
        return f"/psychotest/tes/{self.token}/"


# ─────────────────────────────────────────────────────────────────────────────
# JAWABAN KANDIDAT
# ─────────────────────────────────────────────────────────────────────────────

class PsikotesAnswer(models.Model):
    """Menyimpan jawaban kandidat per soal."""
    session     = models.ForeignKey(PsikotesSession, on_delete=models.CASCADE,
                                    related_name='answers')
    soal        = models.ForeignKey(SoalBank, on_delete=models.CASCADE)
    jawaban     = models.CharField(max_length=1, blank=True,
                                   help_text='A/B/C/D yang dipilih kandidat')
    # Khusus DISC: kandidat pilih MOST (paling) dan LEAST (kurang)
    disc_most   = models.CharField(max_length=1, blank=True)
    disc_least  = models.CharField(max_length=1, blank=True)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('session', 'soal')
        verbose_name = 'Jawaban Psikotes'

    @property
    def is_correct(self):
        if self.soal.tipe == 'pilihan_ganda' and self.soal.jawaban_benar:
            return self.jawaban == self.soal.jawaban_benar
        return None


# ─────────────────────────────────────────────────────────────────────────────
# HASIL PSIKOTES
# ─────────────────────────────────────────────────────────────────────────────

class PsikotesResult(models.Model):
    """Hasil akhir psikotes setelah kandidat submit."""
    session     = models.OneToOneField(PsikotesSession, on_delete=models.CASCADE,
                                       related_name='result')
    candidate   = models.OneToOneField(
        'recruitment.Candidate',
        on_delete=models.CASCADE,
        related_name='psychotest_result'
    )

    # Skor per kategori (0-100)
    skor_logika     = models.IntegerField(null=True, blank=True)
    skor_verbal     = models.IntegerField(null=True, blank=True)
    skor_numerik    = models.IntegerField(null=True, blank=True)
    skor_total      = models.IntegerField(null=True, blank=True,
                                          verbose_name='Skor Total Psikotes (0-100)')

    # DISC
    disc_d          = models.IntegerField(default=0, verbose_name='DISC - Dominance')
    disc_i          = models.IntegerField(default=0, verbose_name='DISC - Influence')
    disc_s          = models.IntegerField(default=0, verbose_name='DISC - Steadiness')
    disc_c          = models.IntegerField(default=0, verbose_name='DISC - Conscientiousness')
    disc_profil     = models.CharField(max_length=5, blank=True,
                                       verbose_name='Profil DISC dominan (misal: D, IS, SC)')
    disc_deskripsi  = models.TextField(blank=True)

    # Detail skor mentah
    detail          = models.JSONField(default=dict,
                                       verbose_name='Detail hasil (benar/salah per soal)')

    # Catatan / interpretasi HR
    catatan_hr      = models.TextField(blank=True)
    grade           = models.CharField(max_length=2, blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hasil Psikotes'
        verbose_name_plural = 'Hasil Psikotes'

    def __str__(self):
        return f"Hasil Psikotes — {self.candidate.nama} — Skor: {self.skor_total}"

    @property
    def disc_dominant(self):
        """Dimensi DISC dengan nilai tertinggi."""
        scores = {'D': self.disc_d, 'I': self.disc_i, 'S': self.disc_s, 'C': self.disc_c}
        return max(scores, key=scores.get)

    @property
    def disc_chart_data(self):
        return {
            'labels': ['Dominance (D)', 'Influence (I)', 'Steadiness (S)', 'Conscientiousness (C)'],
            'data':   [self.disc_d, self.disc_i, self.disc_s, self.disc_c],
        }

    def compute_grade(self):
        s = self.skor_total or 0
        if s >= 80: return 'A'
        if s >= 65: return 'B'
        if s >= 50: return 'C'
        return 'D'


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE — TAHAP TAMBAHAN
# ─────────────────────────────────────────────────────────────────────────────

class MedicalCheckUp(models.Model):
    """Tahap 4 — Medical Check Up."""
    STATUS_CHOICES = [
        ('pending', 'Belum MCU'),
        ('fit',     'Fit'),
        ('fit_note','Fit with Note'),
        ('unfit',   'Unfit'),
    ]
    candidate       = models.OneToOneField(
        'recruitment.Candidate', on_delete=models.CASCADE,
        related_name='medical_checkup'
    )
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    tanggal_mcu     = models.DateField(null=True, blank=True, verbose_name='Tanggal MCU')
    faskes          = models.CharField(max_length=200, blank=True, verbose_name='Fasilitas Kesehatan')
    catatan         = models.TextField(blank=True, verbose_name='Catatan / Diagnosis')
    file_hasil      = models.FileField(upload_to='mcu/', null=True, blank=True,
                                       verbose_name='File Hasil MCU')
    approved_by     = models.CharField(max_length=100, blank=True)
    approved_at     = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Medical Check Up'

    def __str__(self):
        return f"MCU — {self.candidate.nama} — {self.get_status_display()}"


class InterviewSession(models.Model):
    """Tahap 6 — Interview (bisa lebih dari 1 sesi per kandidat)."""
    TIPE_CHOICES = [
        ('hr',   'Interview HR'),
        ('user', 'Interview User / Manager'),
        ('final','Final Interview'),
    ]
    candidate       = models.ForeignKey(
        'recruitment.Candidate', on_delete=models.CASCADE,
        related_name='interview_sessions'
    )
    tipe            = models.CharField(max_length=10, choices=TIPE_CHOICES, default='hr')
    interviewer     = models.CharField(max_length=200, verbose_name='Nama Interviewer')
    tanggal         = models.DateField(verbose_name='Tanggal Interview')
    jam             = models.TimeField(null=True, blank=True)
    lokasi          = models.CharField(max_length=200, blank=True,
                                       help_text='Ruang / Link Zoom / Google Meet')

    # Nilai per aspek (0-100)
    nilai_technical     = models.IntegerField(null=True, blank=True, verbose_name='Technical / Knowledge')
    nilai_attitude      = models.IntegerField(null=True, blank=True, verbose_name='Attitude')
    nilai_communication = models.IntegerField(null=True, blank=True, verbose_name='Communication')
    nilai_culture_fit   = models.IntegerField(null=True, blank=True, verbose_name='Culture Fit')
    catatan             = models.TextField(blank=True, verbose_name='Catatan Interviewer')
    rekomendasi         = models.CharField(max_length=20, blank=True,
                                           choices=[('lanjut','Lanjutkan'),
                                                    ('pertimbangkan','Pertimbangkan'),
                                                    ('tolak','Tolak')])
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sesi Interview'
        verbose_name_plural = 'Sesi Interview'
        ordering = ['-tanggal']

    def __str__(self):
        return f"Interview {self.get_tipe_display()} — {self.candidate.nama} — {self.tanggal}"

    @property
    def skor_rata(self):
        vals = [v for v in [self.nilai_technical, self.nilai_attitude,
                             self.nilai_communication, self.nilai_culture_fit] if v is not None]
        return round(sum(vals) / len(vals)) if vals else None


class Rekomendasi(models.Model):
    """Tahap 5 — Keputusan HR setelah semua tahap assessment."""
    KEPUTUSAN_CHOICES = [
        ('lanjut_offering', 'Lanjut ke Offering Letter'),
        ('tolak',           'Tolak Kandidat'),
        ('hold',            'Hold / Tunda'),
    ]
    candidate   = models.OneToOneField(
        'recruitment.Candidate', on_delete=models.CASCADE,
        related_name='rekomendasi'
    )
    keputusan   = models.CharField(max_length=20, choices=KEPUTUSAN_CHOICES)
    alasan      = models.TextField(blank=True, verbose_name='Alasan / Catatan')
    approved_by = models.CharField(max_length=100, blank=True, verbose_name='Diputuskan oleh')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rekomendasi HR'

    def __str__(self):
        return f"Rekomendasi — {self.candidate.nama} — {self.get_keputusan_display()}"


class OnboardingChecklist(models.Model):
    """Tahap 8 — Onboarding checklist dokumen + orientasi."""
    candidate       = models.OneToOneField(
        'recruitment.Candidate', on_delete=models.CASCADE,
        related_name='onboarding'
    )
    tanggal_mulai   = models.DateField(null=True, blank=True, verbose_name='Tanggal Mulai Kerja')
    masa_probasi    = models.IntegerField(default=3, verbose_name='Masa Probasi (bulan)')

    # Dokumen wajib
    doc_ktp         = models.BooleanField(default=False, verbose_name='KTP')
    doc_ijazah      = models.BooleanField(default=False, verbose_name='Ijazah')
    doc_skck        = models.BooleanField(default=False, verbose_name='SKCK')
    doc_foto        = models.BooleanField(default=False, verbose_name='Foto 4x6')
    doc_npwp        = models.BooleanField(default=False, verbose_name='NPWP')
    doc_bpjs        = models.BooleanField(default=False, verbose_name='Kartu BPJS')
    doc_rekening    = models.BooleanField(default=False, verbose_name='Buku Rekening')
    doc_kontrak     = models.BooleanField(default=False, verbose_name='Kontrak Kerja Ditandatangani')

    # Orientasi
    ori_perkenalan  = models.BooleanField(default=False, verbose_name='Perkenalan Tim')
    ori_sop         = models.BooleanField(default=False, verbose_name='Penjelasan SOP')
    ori_fasilitas   = models.BooleanField(default=False, verbose_name='Pengenalan Fasilitas')
    ori_sistem      = models.BooleanField(default=False, verbose_name='Akses Sistem / Email')

    catatan         = models.TextField(blank=True)
    selesai         = models.BooleanField(default=False, verbose_name='Onboarding Selesai')
    employee_created= models.BooleanField(default=False, verbose_name='Employee Record Dibuat')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Onboarding Checklist'

    def __str__(self):
        return f"Onboarding — {self.candidate.nama}"

    @property
    def doc_progress(self):
        fields = [self.doc_ktp, self.doc_ijazah, self.doc_skck, self.doc_foto,
                  self.doc_npwp, self.doc_bpjs, self.doc_rekening, self.doc_kontrak]
        done = sum(1 for f in fields if f)
        return {'done': done, 'total': len(fields), 'pct': round(done / len(fields) * 100)}

    @property
    def ori_progress(self):
        fields = [self.ori_perkenalan, self.ori_sop, self.ori_fasilitas, self.ori_sistem]
        done = sum(1 for f in fields if f)
        return {'done': done, 'total': len(fields), 'pct': round(done / len(fields) * 100)}
