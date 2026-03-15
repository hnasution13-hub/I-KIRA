from django.db import models
from django.urls import reverse

class Vendor(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='Aktif', choices=[('Aktif', 'Aktif'), ('Tidak Aktif', 'Tidak Aktif')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendor'

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_absolute_url(self):
        return reverse('vendors:vendor_detail', args=[self.pk])