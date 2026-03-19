"""
apps/recruitment/models_profile.py

Model untuk Portal Kandidat:
  - CandidateProfile : data diri lengkap kandidat (diisi mandiri via token)
  - CandidateAnak    : data anak kandidat
"""
import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta


def profile_foto_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return f'candidate_profile/{instance.candidate_id}/foto.{ext}'


def profile_doc_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    field_name = 'doc'
    return f'candidate_profile/{instance.candidate_id}/{field_name}_{filename}'


# Fungsi upload individual — menggantikan closure _doc_upload
# Django migration serializer tidak bisa serialize fungsi hasil closure
def upload_foto(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return f'candidate_profile/{instance.candidate_id}/foto.{ext}'


def upload_ktp(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return f'candidate_profile/{instance.candidate_id}/ktp.{ext}'


def upload_ijazah(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return f'candidate_profile/{instance.candidate_id}/ijazah.{ext}'


def upload_skck(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return f'candidate_profile/{instance.candidate_id}/skck.{ext}'


def upload_npwp(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return f'candidate_profile/{instance.candidate_id}/npwp.{ext}'


def default_token_expires():
    return timezone.now() + timedelta(days=30)


class CandidateProfile(models.Model):
    JENIS_KELAMIN_CHOICES = [('L', 'Laki-laki'), ('P', 'Perempuan')]
    AGAMA_CHOICES = [
        ('Islam', 'Islam'), ('Kristen', 'Kristen'), ('Katolik', 'Katolik'),
        ('Hindu', 'Hindu'), ('Buddha', 'Buddha'), ('Konghucu', 'Konghucu'),
    ]
    GOLONGAN_DARAH_CHOICES = [
        ('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O'),
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ]
    STATUS_NIKAH_CHOICES = [
        ('Lajang', 'Lajang'), ('Menikah', 'Menikah'), ('Cerai', 'Cerai'),
    ]
    PTKP_CHOICES = [
        ('TK/0', 'TK/0'), ('TK/1', 'TK/1'), ('TK/2', 'TK/2'), ('TK/3', 'TK/3'),
        ('K/0', 'K/0'), ('K/1', 'K/1'), ('K/2', 'K/2'), ('K/3', 'K/3'),
        ('K/I/0', 'K/I/0'), ('K/I/1', 'K/I/1'), ('K/I/2', 'K/I/2'), ('K/I/3', 'K/I/3'),
    ]
    PENDIDIKAN_CHOICES = [
        ('SD', 'SD'), ('SMP', 'SMP'), ('SMA/SMK', 'SMA/SMK'),
        ('D1', 'D1'), ('D2', 'D2'), ('D3', 'D3'),
        ('D4/S1', 'D4/S1'), ('S2', 'S2'), ('S3', 'S3'),
    ]

    # ── Relasi ────────────────────────────────────────────────────────────────
    candidate       = models.OneToOneField(
        'recruitment.Candidate',
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Kandidat',
    )

    # ── Token akses publik ────────────────────────────────────────────────────
    token           = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    token_created_at = models.DateTimeField(auto_now_add=True)
    token_expires_at = models.DateTimeField(default=default_token_expires)

    # ── Status pengisian ──────────────────────────────────────────────────────
    is_submitted    = models.BooleanField(default=False, verbose_name='Sudah Diisi')
    submitted_at    = models.DateTimeField(null=True, blank=True)
    is_reviewed     = models.BooleanField(default=False, verbose_name='Sudah Di-review HR')
    reviewed_by     = models.CharField(max_length=100, blank=True)
    reviewed_at     = models.DateTimeField(null=True, blank=True)

    # ── Data Pribadi ──────────────────────────────────────────────────────────
    tempat_lahir    = models.CharField(max_length=100, blank=True, verbose_name='Tempat Lahir')
    tanggal_lahir   = models.DateField(null=True, blank=True, verbose_name='Tanggal Lahir')
    jenis_kelamin   = models.CharField(max_length=1, choices=JENIS_KELAMIN_CHOICES,
                                       blank=True, verbose_name='Jenis Kelamin')
    agama           = models.CharField(max_length=20, choices=AGAMA_CHOICES,
                                       blank=True, verbose_name='Agama')
    pendidikan      = models.CharField(max_length=10, choices=PENDIDIKAN_CHOICES,
                                       blank=True, verbose_name='Pendidikan Terakhir')
    golongan_darah  = models.CharField(max_length=4, choices=GOLONGAN_DARAH_CHOICES,
                                       blank=True, verbose_name='Golongan Darah')
    status_nikah    = models.CharField(max_length=10, choices=STATUS_NIKAH_CHOICES,
                                       blank=True, verbose_name='Status Pernikahan')
    jumlah_anak     = models.PositiveSmallIntegerField(default=0, verbose_name='Jumlah Anak')
    ptkp            = models.CharField(max_length=10, choices=PTKP_CHOICES,
                                       blank=True, verbose_name='PTKP')

    # ── Dokumen Identitas ─────────────────────────────────────────────────────
    no_ktp          = models.CharField(max_length=20, blank=True, verbose_name='No. KTP')
    no_kk           = models.CharField(max_length=20, blank=True, verbose_name='No. KK')
    no_npwp         = models.CharField(max_length=25, blank=True, verbose_name='No. NPWP')
    no_bpjs_kes     = models.CharField(max_length=30, blank=True, verbose_name='No. BPJS Kesehatan')
    no_bpjs_tk      = models.CharField(max_length=30, blank=True, verbose_name='No. BPJS Ketenagakerjaan')

    # ── Rekening ──────────────────────────────────────────────────────────────
    no_rek          = models.CharField(max_length=30, blank=True, verbose_name='No. Rekening')
    nama_bank       = models.CharField(max_length=200, blank=True, verbose_name='Nama Bank')
    nama_rek        = models.CharField(max_length=100, blank=True, verbose_name='Nama di Rekening')

    # ── Alamat ────────────────────────────────────────────────────────────────
    alamat          = models.TextField(blank=True, verbose_name='Alamat Lengkap')
    rt              = models.CharField(max_length=5, blank=True, verbose_name='RT')
    rw              = models.CharField(max_length=5, blank=True, verbose_name='RW')
    kode_pos        = models.CharField(max_length=10, blank=True, verbose_name='Kode Pos')
    provinsi        = models.ForeignKey('wilayah.Provinsi', on_delete=models.SET_NULL,
                                        null=True, blank=True, verbose_name='Provinsi')
    kabupaten       = models.ForeignKey('wilayah.Kabupaten', on_delete=models.SET_NULL,
                                        null=True, blank=True, verbose_name='Kabupaten/Kota')
    kecamatan       = models.CharField(max_length=100, blank=True, verbose_name='Kecamatan')
    kelurahan       = models.CharField(max_length=100, blank=True, verbose_name='Kelurahan/Desa')

    # ── Kontak Darurat ────────────────────────────────────────────────────────
    nama_darurat    = models.CharField(max_length=100, blank=True, verbose_name='Nama Kontak Darurat')
    hub_darurat     = models.CharField(max_length=50, blank=True, verbose_name='Hubungan')
    hp_darurat      = models.CharField(max_length=20, blank=True, verbose_name='No. HP Darurat')

    # ── Upload Dokumen ────────────────────────────────────────────────────────
    foto            = models.ImageField(upload_to=upload_foto,
                                        null=True, blank=True, verbose_name='Foto')
    scan_ktp        = models.FileField(upload_to=upload_ktp,
                                       null=True, blank=True, verbose_name='Scan KTP')
    scan_ijazah     = models.FileField(upload_to=upload_ijazah,
                                       null=True, blank=True, verbose_name='Scan Ijazah')
    scan_skck       = models.FileField(upload_to=upload_skck,
                                       null=True, blank=True, verbose_name='Scan SKCK')
    scan_npwp       = models.FileField(upload_to=upload_npwp,
                                       null=True, blank=True, verbose_name='Scan NPWP')

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Profil Kandidat'
        verbose_name_plural = 'Profil Kandidat'

    def __str__(self):
        return f'Profil — {self.candidate.nama}'

    @property
    def is_token_valid(self):
        return timezone.now() <= self.token_expires_at

    @property
    def form_url_path(self):
        return f'/recruitment/portal/{self.token}/'

    def regenerate_token(self):
        """Generate token baru — token lama otomatis invalid."""
        self.token = uuid.uuid4()
        self.token_expires_at = timezone.now() + timedelta(days=30)
        self.save(update_fields=['token', 'token_expires_at'])

    @property
    def completion_pct(self):
        """Persentase kelengkapan data yang diisi."""
        fields = [
            self.tempat_lahir, self.tanggal_lahir, self.jenis_kelamin,
            self.agama, self.no_ktp, self.no_rek, self.nama_bank,
            self.alamat, self.nama_darurat, self.hp_darurat,
        ]
        filled = sum(1 for f in fields if f)
        return round(filled / len(fields) * 100)


class CandidateAnak(models.Model):
    profile         = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE,
                                        related_name='anak_list', verbose_name='Profil')
    urutan          = models.PositiveSmallIntegerField(verbose_name='Urutan')
    nama            = models.CharField(max_length=200, verbose_name='Nama Anak')
    tgl_lahir       = models.DateField(null=True, blank=True, verbose_name='Tgl Lahir')
    jenis_kelamin   = models.CharField(max_length=1,
                                       choices=[('L', 'Laki-laki'), ('P', 'Perempuan')],
                                       blank=True)
    no_bpjs_kes     = models.CharField(max_length=30, blank=True, verbose_name='No. BPJS Kes')

    class Meta:
        verbose_name    = 'Data Anak Kandidat'
        ordering        = ['urutan']
        unique_together = [['profile', 'urutan']]

    def __str__(self):
        return f'{self.nama} (Anak ke-{self.urutan} — {self.profile.candidate.nama})'
