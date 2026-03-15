# ==================================================
# FILE: apps/custom_categories/models.py
# PATH: D:/Project Pyton/Asset Management Django/apps/custom_categories/models.py
# DESKRIPSI: Model untuk custom kategori (penambahan aset via form khusus)
# VERSION: 1.0.0
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from django.db import models
from apps.assets.models import Category

class CategoryCustom(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='customs')
    custom_field = models.CharField(max_length=255, blank=True, verbose_name="Custom Field")
    asset_name = models.CharField(max_length=200, verbose_name="Nama Asset")
    tag_number = models.CharField(max_length=50, unique=True, verbose_name="Nomor Tag")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Custom Kategori"
        verbose_name_plural = "Custom Kategori"
        ordering = ['tag_number']

    def __str__(self):
        return f"{self.tag_number} - {self.asset_name}"