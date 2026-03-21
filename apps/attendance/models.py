from django.db import models
from apps.employees.models import Employee
from apps.core.models import Company


class Holiday(models.Model):
    TIPE_CHOICES = [
        ('Nasional',  'Nasional (SKB/Keppres)'),
        ('Bersama',   'Cuti Bersama'),
        ('Internal',  'Kebijakan Perusahaan'),
    ]
    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='holidays')
    nama       = models.CharField(max_length=200, verbose_name='Nama Hari Libur')
    tanggal    = models.DateField()
    tipe       = models.CharField(max_length=20, choices=TIPE_CHOICES, default='Nasional',
                                   verbose_name='Tipe Libur')
    keterangan = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name        = 'Hari Libur'
        verbose_name_plural = 'Hari Libur'
        ordering            = ['tanggal']
        unique_together     = [['company', 'tanggal']]

    def __str__(self):
        return f"{self.nama} ({self.tanggal})"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Hadir', 'Hadir'),
        ('Tidak Hadir', 'Tidak Hadir'),
        ('Izin', 'Izin'),
        ('Sakit', 'Sakit'),
        ('Cuti', 'Cuti'),
        ('Libur', 'Libur'),
        ('WFH', 'WFH'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    tanggal = models.DateField()
    check_in = models.TimeField(null=True, blank=True, verbose_name='Jam Masuk')
    check_out = models.TimeField(null=True, blank=True, verbose_name='Jam Keluar')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Hadir')
    keterlambatan = models.IntegerField(default=0, help_text='Menit keterlambatan')
    lembur_jam = models.DecimalField(max_digits=4, decimal_places=1, default=0,
                                     verbose_name='Jam Lembur')
    lembur_upah = models.BigIntegerField(default=0, verbose_name='Upah Lembur')
    keterangan = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Absensi'
        verbose_name_plural = 'Absensi'
        ordering = ['-tanggal']
        unique_together = ['employee', 'tanggal']

    def __str__(self):
        return f"{self.employee.nama} - {self.tanggal} - {self.status}"


class Leave(models.Model):
    TIPE_CHOICES = [
        ('Cuti Tahunan', 'Cuti Tahunan'),
        ('Cuti Sakit', 'Cuti Sakit'),
        ('Cuti Melahirkan', 'Cuti Melahirkan'),
        ('Cuti Besar', 'Cuti Besar'),
        ('Cuti Penting', 'Cuti Penting'),
        ('Ijin', 'Ijin'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Disetujui'),
        ('Rejected', 'Ditolak'),
        ('Cancelled', 'Dibatalkan'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    tipe_cuti = models.CharField(max_length=30, choices=TIPE_CHOICES, verbose_name='Tipe Cuti')
    tanggal_mulai = models.DateField(verbose_name='Tanggal Mulai')
    tanggal_selesai = models.DateField(verbose_name='Tanggal Selesai')
    jumlah_hari = models.IntegerField(default=1, verbose_name='Jumlah Hari')
    alasan = models.TextField(verbose_name='Alasan')
    dokumen = models.FileField(upload_to='leave_docs/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    catatan_approval = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cuti / Ijin'
        verbose_name_plural = 'Cuti / Ijin'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.nama} - {self.tipe_cuti} ({self.tanggal_mulai})"
