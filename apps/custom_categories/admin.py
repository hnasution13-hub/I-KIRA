# ==================================================
# FILE: apps/custom_categories/admin.py
# PATH: D:/Project Pyton/Asset Management Django/apps/custom_categories/admin.py
# DESKRIPSI: Admin registration untuk custom kategori
# VERSION: 1.0.0
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from django.contrib import admin
from .models import CategoryCustom

@admin.register(CategoryCustom)
class CategoryCustomAdmin(admin.ModelAdmin):
    list_display = ['tag_number', 'asset_name', 'category', 'custom_field', 'created_at']
    list_filter = ['category']
    search_fields = ['tag_number', 'asset_name']