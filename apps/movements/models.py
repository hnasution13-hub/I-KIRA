from django.db import models
from django.conf import settings
from django.urls import reverse
from apps.assets.models import Asset
from apps.employees.models import Employee
from apps.locations.models import Location

class Movement(models.Model):
    MOVEMENT_TYPES = [
        ('PENUGASAN', 'Penugasan'),
        ('PENGEMBALIAN', 'Pengembalian'),
        ('SERVICE', 'Service'),
        ('MUTASI', 'Mutasi'),
        ('HILANG', 'Hilang'),
        ('DIJUAL', 'Dijual'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='movements')
    asset_code = models.CharField(max_length=50, blank=True)  # denormalized
    movement_date = models.DateField()
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)

    # Dari
    from_pic = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_from')
    from_pic_name = models.CharField(max_length=100, blank=True)
    from_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_from')
    from_location_name = models.CharField(max_length=100, blank=True)
    from_condition = models.CharField(max_length=50, blank=True)

    # Ke
    to_pic = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_to')
    to_pic_name = models.CharField(max_length=100, blank=True)
    to_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_to')
    to_location_name = models.CharField(max_length=100, blank=True)
    to_condition = models.CharField(max_length=50, blank=True)

    # Dokumen
    document_no = models.CharField(max_length=50, blank=True)
    document_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-movement_date', '-created_at']
        verbose_name = 'Mutasi Aset'
        verbose_name_plural = 'Mutasi Aset'

    def __str__(self):
        return f"{self.movement_type} - {self.asset} ({self.movement_date})"

    def save(self, *args, **kwargs):
        # denormalize
        if self.asset and not self.asset_code:
            self.asset_code = self.asset.asset_code
        if self.from_pic and not self.from_pic_name:
            self.from_pic_name = str(self.from_pic)
        if self.to_pic and not self.to_pic_name:
            self.to_pic_name = str(self.to_pic)
        if self.from_location and not self.from_location_name:
            self.from_location_name = self.from_location.name
        if self.to_location and not self.to_location_name:
            self.to_location_name = self.to_location.name
        super().save(*args, **kwargs)


class Assignment(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name='current_assignment')
    asset_code = models.CharField(max_length=50, blank=True)
    current_pic = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_assignments')
    current_pic_name = models.CharField(max_length=100, blank=True)
    current_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_assignments')
    current_location_name = models.CharField(max_length=100, blank=True)
    current_condition = models.CharField(max_length=50, blank=True)
    assignment_date = models.DateField(null=True, blank=True)
    last_movement = models.ForeignKey(Movement, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    last_movement_date = models.DateField(null=True, blank=True)
    expected_return_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Penugasan Aset'
        verbose_name_plural = 'Penugasan Aset'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Assignment: {self.asset} -> {self.current_pic_name or '-'}"

    def save(self, *args, **kwargs):
        if self.asset and not self.asset_code:
            self.asset_code = self.asset.asset_code
        if self.current_pic and not self.current_pic_name:
            self.current_pic_name = str(self.current_pic)
        if self.current_location and not self.current_location_name:
            self.current_location_name = self.current_location.name
        super().save(*args, **kwargs)