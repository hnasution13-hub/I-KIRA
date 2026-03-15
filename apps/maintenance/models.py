from django.db import models
from django.urls import reverse
from apps.assets.models import Asset

class Maintenance(models.Model):
    MAINTENANCE_TYPES = [
        ('Rutin', 'Rutin'),
        ('Perbaikan', 'Perbaikan'),
        ('Kalibrasi', 'Kalibrasi'),
        ('Inspeksi', 'Inspeksi'),
        ('Darurat', 'Darurat'),
    ]
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenances')
    asset_name = models.CharField(max_length=200, blank=True)  # denormalized
    maintenance_date = models.DateField()
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES, default='Rutin')
    description = models.TextField(blank=True)
    technician = models.CharField(max_length=100, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-maintenance_date']
        verbose_name = 'Maintenance'
        verbose_name_plural = 'Maintenance'

    def __str__(self):
        return f"{self.asset} - {self.maintenance_type} ({self.maintenance_date})"

    def save(self, *args, **kwargs):
        if self.asset and not self.asset_name:
            self.asset_name = str(self.asset)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('maintenance:maintenance_detail', args=[self.pk])