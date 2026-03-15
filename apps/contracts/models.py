from django.db import models
from apps.employees.models import Employee
from apps.core.models import Company
from datetime import date


class Contract(models.Model):
    TIPE_CHOICES = [
        ('Perjanjian Harian Lepas', 'Perjanjian Harian Lepas'),
        ('Borongan', 'Borongan'),
        ('PKWT', 'Perjanjian Kerja Waktu Tertentu (PKWT)'),
        ('PKWTT', 'Perjanjian Kerja Waktu Tidak Tertentu (PKWTT)'),
    ]
    STATUS_CHOICES = [
        ('Aktif', 'Aktif'),
        ('Expired', 'Expired'),
        ('Terminated', 'Terminated'),
        ('Renewed', 'Diperpanjang'),
    ]

    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contracts', verbose_name='Perusahaan')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='contracts')
    nomor_kontrak = models.CharField(max_length=50, unique=True, verbose_name='Nomor Kontrak')
    tipe_kontrak = models.CharField(max_length=50, choices=TIPE_CHOICES, verbose_name='Tipe Kontrak')
    tanggal_mulai = models.DateField(verbose_name='Tanggal Mulai')
    tanggal_selesai = models.DateField(null=True, blank=True, verbose_name='Tanggal Selesai')
    jabatan = models.CharField(max_length=100, blank=True)
    departemen = models.CharField(max_length=100, blank=True)
    gaji_pokok = models.BigIntegerField(default=0, verbose_name='Gaji Pokok')
    STATUS_GAJI_CHOICES = [('reguler', 'Reguler'), ('all_in', 'All-In')]
    status_gaji = models.CharField(max_length=10, choices=STATUS_GAJI_CHOICES, default='reguler', verbose_name='Status Gaji')
    nama_penandatangan = models.CharField(max_length=100, blank=True, verbose_name='Nama Penandatangan')
    jabatan_penandatangan = models.CharField(max_length=100, blank=True, verbose_name='Jabatan Penandatangan')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Aktif')
    file_kontrak = models.FileField(upload_to='contracts/', null=True, blank=True)
    keterangan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kontrak'
        verbose_name_plural = 'Kontrak'
        ordering = ['-tanggal_mulai']

    def __str__(self):
        return f"{self.nomor_kontrak} - {self.employee.nama}"

    def save(self, *args, **kwargs):
        if not self.nomor_kontrak:
            self.nomor_kontrak = self._generate_number()
        # FIX BUG-008: Tangkap IntegrityError jika nomor bentrok (race condition)
        from django.db import IntegrityError
        max_retries = 5
        for attempt in range(max_retries):
            try:
                super().save(*args, **kwargs)
                return
            except IntegrityError:
                if attempt < max_retries - 1:
                    self.nomor_kontrak = self._generate_number()
                else:
                    raise

    def _generate_number(self):
        from datetime import datetime
        now = datetime.now()
        count = Contract.objects.filter(
            nomor_kontrak__startswith=f"CTR/{now.year}"
        ).count()
        return f"CTR/{now.year}{now.month:02d}/{count + 1:04d}"

    @property
    def sisa_hari(self):
        if self.tanggal_selesai:
            delta = self.tanggal_selesai - date.today()
            return delta.days
        return None

    @property
    def is_expiring_soon(self):
        sisa = self.sisa_hari
        return sisa is not None and 0 <= sisa <= 30
