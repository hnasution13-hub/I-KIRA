from django.db import models
from django.conf import settings


class BiodataChangeLog(models.Model):
    """Log setiap perubahan biodata yang dilakukan karyawan via portal."""
    employee    = models.ForeignKey('employees.Employee', on_delete=models.CASCADE,
                                    related_name='biodata_logs', verbose_name='Karyawan')
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name='Diubah oleh')
    field_name  = models.CharField(max_length=100, verbose_name='Field')
    label       = models.CharField(max_length=100, verbose_name='Label Field')
    nilai_lama  = models.TextField(blank=True, verbose_name='Nilai Lama')
    nilai_baru  = models.TextField(blank=True, verbose_name='Nilai Baru')
    waktu       = models.DateTimeField(auto_now_add=True, verbose_name='Waktu Perubahan')

    class Meta:
        verbose_name        = 'Log Perubahan Biodata'
        verbose_name_plural = 'Log Perubahan Biodata'
        ordering            = ['-waktu']

    def __str__(self):
        return f'{self.employee.nama} — {self.label} [{self.waktu:%d/%m/%Y %H:%M}]'
