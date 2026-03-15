# ==================================================
# FILE: apps/assets/models.py
# PATH: D:/Project Pyton/Asset Management Django/apps/assets/models.py
# DESKRIPSI: Model Asset, Kategori, Depresiasi
# PERBAIKAN: Tambah validasi monthly_depreciation jika useful_life=0
# VERSION: 1.0.2
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from django.db import models
from django.conf import settings
from apps.employees.models import Employee
from apps.core.models import Company
from apps.vendors.models import Vendor
from apps.locations.models import Location


class Category(models.Model):
    ASSET_TYPE_CHOICES = (
        ('Tangible', 'Berwujud'),
        ('Intangible', 'Tidak Berwujud'),
        ('Custom', 'Custom'),
    )

    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='asset_categories', verbose_name='Perusahaan')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    asset_type = models.CharField(
        max_length=20,
        choices=ASSET_TYPE_CHOICES,
        default='Tangible'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Kategori'
        verbose_name_plural = 'Kategori'

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_full_path(self):
        path = [self.name]
        current = self.parent
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' > '.join(path)


class Asset(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('MAINTENANCE', 'Maintenance'),
        ('RETIRED', 'Retired'),
        ('BROKEN', 'Broken'),
        ('RESERVED', 'Reserved'),
    )
    CONDITION_CHOICES = (
        ('Baik', 'Baik'),
        ('Rusak Ringan', 'Rusak Ringan'),
        ('Rusak Berat', 'Rusak Berat'),
        ('Dalam Perbaikan', 'Dalam Perbaikan'),
    )

    company    = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='assets', verbose_name='Perusahaan')
    asset_code = models.CharField(max_length=50, unique=True)
    asset_name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    purchase_date = models.DateField()
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2)
    useful_life = models.IntegerField(default=5)  # tahun
    residual_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    serial_number = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='Baik'
    )
    warranty_date = models.DateField(null=True, blank=True)
    responsible = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets'
    )
    cabinet = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Lemari/Rak"
    )
    invoice = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nomor Nota"
    )
    notes = models.TextField(blank=True)
    photo = models.ImageField(upload_to='assets/', null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets_updated'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"

    def book_value(self):
        last_dep = self.depreciation_set.order_by('-year', '-month').first()
        if last_dep:
            return last_dep.book_value
        return self.purchase_price

    def monthly_depreciation(self):
        """Menghitung depresiasi bulanan dengan aman."""
        if self.useful_life > 0:
            return (self.purchase_price - self.residual_value) / (self.useful_life * 12)
        return 0  # jika masa manfaat 0, tidak ada depresiasi


class Depreciation(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    monthly_depreciation = models.DecimalField(max_digits=15, decimal_places=2)
    accumulated_depreciation = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    book_value = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = ['asset', 'year', 'month']
        ordering = ['asset', 'year', 'month']
        verbose_name = 'Depresiasi'
        verbose_name_plural = 'Depresiasi'

    def __str__(self):
        return f"{self.asset.asset_code} - {self.year}-{self.month:02d}"


class DepreciationValue(models.Model):
    METHOD_CHOICES = (
        ('Garis Lurus', 'Garis Lurus (Straight Line)'),
        ('Saldo Menurun', 'Saldo Menurun (Declining Balance)'),
        ('Saldo Menurun Ganda', 'Saldo Menurun Ganda (Double Declining)'),
        ('Jumlah Angka Tahun', 'Jumlah Angka Tahun (Sum of Years)'),
        ('Unit Produksi', 'Unit Produksi (Units of Production)'),
    )

    category = models.CharField(max_length=100)
    method = models.CharField(
        max_length=50,
        choices=METHOD_CHOICES,
        default='Garis Lurus'
    )
    useful_life = models.IntegerField(default=5)
    residual_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10
    )
    rate = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Nilai Penyusutan'
        verbose_name_plural = 'Nilai Penyusutan'

    def __str__(self):
        return f"{self.category} - {self.method}"