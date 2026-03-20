from django.db import models
from django.utils import timezone
from django.conf import settings
from apps.core.models import Company, Department, Position


class PointOfHire(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='point_of_hires')
    nama    = models.CharField(max_length=100, verbose_name='Point of Hire')
    aktif   = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Point of Hire'
        verbose_name_plural = 'Point of Hire'
        ordering            = ['nama']
        unique_together     = [['company', 'nama']]

    def __str__(self):
        return self.nama


class JobSite(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_sites')
    nama    = models.CharField(max_length=100, verbose_name='Job Site')
    aktif   = models.BooleanField(default=True)

    # ── Geofencing ────────────────────────────────────────────────────────────
    latitude     = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True, verbose_name='Latitude Kantor'
    )
    longitude    = models.DecimalField(
        max_digits=10, decimal_places=7,
        null=True, blank=True, verbose_name='Longitude Kantor'
    )
    radius_meter = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Radius Check-In (meter)',
        help_text='Jarak maksimal dari koordinat kantor. Wajib diset agar check-in dapat dilakukan.'
    )

    class Meta:
        verbose_name        = 'Job Site'
        verbose_name_plural = 'Job Site'
        ordering            = ['nama']
        unique_together     = [['company', 'nama']]

    def __str__(self):
        return self.nama


class Perusahaan(models.Model):
    """Sub-perusahaan/vendor dalam satu company (untuk outsourcing)."""
    company     = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sub_perusahaan')
    nama        = models.CharField(max_length=200, verbose_name='Nama Perusahaan')
    singkatan   = models.CharField(max_length=20, blank=True)
    npwp        = models.CharField(max_length=25, blank=True)
    alamat      = models.TextField(blank=True)
    no_telp     = models.CharField(max_length=20, blank=True)
    email       = models.EmailField(blank=True)
    pic_nama    = models.CharField(max_length=100, blank=True)
    pic_hp      = models.CharField(max_length=20, blank=True)
    aktif       = models.BooleanField(default=True)
    catatan     = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Perusahaan'
        verbose_name_plural = 'Perusahaan'
        ordering            = ['nama']
        unique_together     = [['company', 'nama']]

    def __str__(self):
        return self.singkatan if self.singkatan else self.nama


class Employee(models.Model):
    STATUS_CHOICES = [
        ('Aktif', 'Aktif'), ('Tidak Aktif', 'Tidak Aktif'),
        ('Resign', 'Resign'), ('PHK', 'PHK'), ('Pensiun', 'Pensiun'),
    ]
    JENIS_KELAMIN_CHOICES  = [('L', 'Laki-laki'), ('P', 'Perempuan')]
    STATUS_KARYAWAN_CHOICES = [
        ('Borongan', 'Borongan'), ('PHL', 'PHL'), ('PKWT', 'PKWT'), ('PKWTT', 'PKWTT'),
    ]
    AGAMA_CHOICES = [
        ('Islam','Islam'),('Kristen','Kristen'),('Katolik','Katolik'),
        ('Hindu','Hindu'),('Buddha','Buddha'),('Konghucu','Konghucu'),
    ]
    PENDIDIKAN_CHOICES = [
        ('SD','SD'),('SMP','SMP'),('SMA/SMK','SMA/SMK'),
        ('D1','D1'),('D2','D2'),('D3','D3'),('D4/S1','D4/S1'),('S2','S2'),('S3','S3'),
    ]
    GOLONGAN_DARAH_CHOICES = [
        ('A','A'),('B','B'),('AB','AB'),('O','O'),
        ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
        ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),
    ]
    STATUS_NIKAH_CHOICES = [('Lajang','Lajang'),('Menikah','Menikah'),('Cerai','Cerai')]
    PTKP_CHOICES = [
        ('TK/0','TK/0'),('TK/1','TK/1'),('TK/2','TK/2'),('TK/3','TK/3'),
        ('K/0','K/0'),('K/1','K/1'),('K/2','K/2'),('K/3','K/3'),
        ('K/I/0','K/I/0'),('K/I/1','K/I/1'),('K/I/2','K/I/2'),('K/I/3','K/I/3'),
    ]

    # TENANT
    company         = models.ForeignKey(Company, on_delete=models.CASCADE,
                                        related_name='employees', verbose_name='Perusahaan')

    # Data Utama
    nik             = models.CharField(max_length=20, verbose_name='NIK')
    nama            = models.CharField(max_length=200, verbose_name='Nama Lengkap')
    department      = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    jabatan         = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    status_karyawan = models.CharField(max_length=10, choices=STATUS_KARYAWAN_CHOICES, default='PKWT')
    join_date       = models.DateField(verbose_name='Tanggal Masuk')
    end_date        = models.DateField(null=True, blank=True, verbose_name='Tanggal Keluar')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Aktif')
    point_of_hire   = models.ForeignKey(PointOfHire, on_delete=models.SET_NULL, null=True, blank=True)
    job_site        = models.ForeignKey(JobSite, on_delete=models.SET_NULL, null=True, blank=True)
    perusahaan      = models.ForeignKey(Perusahaan, on_delete=models.SET_NULL, null=True, blank=True)
    foto            = models.ImageField(upload_to='employee_photos/', null=True, blank=True)
    user            = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name='employee')

    # Data Pribadi
    tempat_lahir    = models.CharField(max_length=100, blank=True)
    tanggal_lahir   = models.DateField(null=True, blank=True)
    jenis_kelamin   = models.CharField(max_length=1, choices=JENIS_KELAMIN_CHOICES, blank=True)
    agama           = models.CharField(max_length=20, choices=AGAMA_CHOICES, blank=True)
    pendidikan      = models.CharField(max_length=10, choices=PENDIDIKAN_CHOICES, blank=True)
    golongan_darah  = models.CharField(max_length=4, choices=GOLONGAN_DARAH_CHOICES, blank=True)
    status_nikah    = models.CharField(max_length=10, choices=STATUS_NIKAH_CHOICES, blank=True)
    jumlah_anak     = models.PositiveSmallIntegerField(default=0)
    ptkp            = models.CharField(max_length=10, choices=PTKP_CHOICES, blank=True)
    no_ktp          = models.CharField(max_length=20, blank=True)
    no_kk           = models.CharField(max_length=20, blank=True)
    no_npwp         = models.CharField(max_length=25, blank=True)
    no_bpjs_kes     = models.CharField(max_length=30, blank=True)
    no_bpjs_tk      = models.CharField(max_length=30, blank=True)
    no_rek          = models.CharField(max_length=30, blank=True)
    nama_bank       = models.CharField(max_length=200, blank=True, verbose_name='Bank')
    nama_rek        = models.CharField(max_length=100, blank=True)
    no_hp           = models.CharField(max_length=20, blank=True)
    email           = models.EmailField(blank=True)

    # Alamat
    alamat          = models.TextField(blank=True)
    rt              = models.CharField(max_length=5, blank=True)
    rw              = models.CharField(max_length=5, blank=True)
    kode_pos        = models.CharField(max_length=10, blank=True)
    provinsi        = models.ForeignKey('wilayah.Provinsi', on_delete=models.SET_NULL,
                                        null=True, blank=True)
    kabupaten       = models.ForeignKey('wilayah.Kabupaten', on_delete=models.SET_NULL,
                                        null=True, blank=True)
    kecamatan       = models.CharField(max_length=100, blank=True)
    kelurahan       = models.CharField(max_length=100, blank=True)

    # Kontak Darurat
    nama_darurat    = models.CharField(max_length=100, blank=True)
    hub_darurat     = models.CharField(max_length=50, blank=True)
    hp_darurat      = models.CharField(max_length=20, blank=True)

    # Gaji
    gaji_pokok      = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Karyawan'
        verbose_name_plural = 'Karyawan'
        ordering            = ['nama']
        unique_together     = [['company', 'nik']]

    def __str__(self):
        return f'{self.nik} — {self.nama}'

    @property
    def usia(self):
        if not self.tanggal_lahir:
            return None
        today = timezone.now().date()
        born  = self.tanggal_lahir
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    @property
    def masa_kerja(self):
        today = timezone.now().date()
        end   = self.end_date or today
        delta = end - self.join_date
        tahun = delta.days // 365
        bulan = (delta.days % 365) // 30
        return tahun, bulan

    @property
    def masa_kerja_display(self):
        tahun, bulan = self.masa_kerja
        if tahun > 0:
            return f'{tahun} tahun {bulan} bulan'
        return f'{bulan} bulan'

    @property
    def masa_kerja_bulan(self):
        tahun, bulan = self.masa_kerja
        return tahun * 12 + bulan


class AnakKaryawan(models.Model):
    employee      = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='anak_list')
    urutan        = models.PositiveSmallIntegerField()
    nama          = models.CharField(max_length=200)
    tgl_lahir     = models.DateField(null=True, blank=True)
    jenis_kelamin = models.CharField(max_length=1, choices=[('L','L'),('P','P')], blank=True)
    no_bpjs_kes   = models.CharField(max_length=30, blank=True)
    tanggungan_bpjs = models.BooleanField(default=True)

    class Meta:
        verbose_name    = 'Anak Karyawan'
        ordering        = ['urutan']
        unique_together = [['employee', 'urutan']]

    def __str__(self):
        return f'{self.nama} (Anak ke-{self.urutan} — {self.employee.nama})'


class EmployeeDocument(models.Model):
    TIPE_CHOICES = [
        ('KTP','KTP'),('NPWP','NPWP'),('Ijazah','Ijazah'),
        ('CV','CV'),('Kontrak','Kontrak'),('SKCK','SKCK'),('Lainnya','Lainnya'),
    ]
    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    tipe        = models.CharField(max_length=20, choices=TIPE_CHOICES)
    nama_file   = models.CharField(max_length=200)
    file        = models.FileField(upload_to='employee_docs/')
    keterangan  = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.employee.nama} - {self.tipe}'


class EmployeeDevice(models.Model):
    """Perangkat terdaftar untuk portal — anti-fraud."""
    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='devices')
    mac_address    = models.CharField(max_length=17, verbose_name='MAC Address / Device ID')
    nama_perangkat = models.CharField(max_length=100, blank=True)
    platform       = models.CharField(max_length=50, blank=True)
    user_agent     = models.TextField(blank=True)
    aktif          = models.BooleanField(default=True)
    terdaftar_oleh = models.CharField(max_length=100, blank=True)
    catatan        = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    last_seen      = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name    = 'Perangkat Karyawan'
        ordering        = ['-created_at']
        unique_together = [['employee', 'mac_address']]

    def __str__(self):
        return f'{self.employee.nama} — {self.mac_address}'


class PortalCheckInLog(models.Model):
    """Log check-in/out portal untuk audit anti-fraud."""
    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='checkin_logs')
    device         = models.ForeignKey(EmployeeDevice, on_delete=models.SET_NULL, null=True, blank=True)
    mac_address    = models.CharField(max_length=17, blank=True)
    latitude       = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude      = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    akurasi_gps    = models.FloatField(null=True, blank=True)
    ip_address     = models.GenericIPAddressField(null=True, blank=True)
    user_agent     = models.TextField(blank=True)
    tipe           = models.CharField(max_length=10, choices=[('checkin','Check-In'),('checkout','Check-Out')])
    waktu          = models.DateTimeField(auto_now_add=True)
    device_dikenal = models.BooleanField(default=False)
    gps_valid      = models.BooleanField(default=False)
    flagged        = models.BooleanField(default=False)
    catatan_flag   = models.TextField(blank=True)

    # ── Geofencing ────────────────────────────────────────────────────────────
    jarak_meter    = models.FloatField(null=True, blank=True, verbose_name='Jarak dari Kantor (m)')
    dalam_radius   = models.BooleanField(null=True, blank=True, verbose_name='Dalam Radius')
    ditolak        = models.BooleanField(default=False, verbose_name='Check-In Ditolak')
    alasan_tolak   = models.TextField(blank=True, verbose_name='Alasan Penolakan')

    class Meta:
        verbose_name = 'Log Check-In Portal'
        ordering     = ['-waktu']

    def __str__(self):
        return f'{self.employee.nama} — {self.tipe} — {self.waktu.strftime("%d/%m/%Y %H:%M")}'
