from django.contrib import admin
from .models import Category, Asset, Depreciation, DepreciationValue

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'asset_type', 'created_at']
    list_filter = ['asset_type', 'parent']
    search_fields = ['name', 'code']

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_code', 'asset_name', 'category', 'status', 'responsible', 'location', 'purchase_price', 'book_value']
    list_filter = ['status', 'category', 'location', 'vendor', 'condition']
    search_fields = ['asset_code', 'asset_name', 'serial_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('asset_code', 'asset_name', 'category', 'notes')
        }),
        ('Keuangan', {
            'fields': ('purchase_date', 'purchase_price', 'residual_value', 'useful_life')
        }),
        ('Status & Penempatan', {
            'fields': ('status', 'condition', 'responsible', 'location', 'cabinet')
        }),
        ('Vendor & Garansi', {
            'fields': ('vendor', 'warranty_date')
        }),
        ('Identifikasi', {
            'fields': ('serial_number', 'brand', 'invoice')
        }),
        ('Media', {
            'fields': ('photo',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def book_value(self, obj):
        return obj.book_value()
    book_value.short_description = 'Nilai Buku'

@admin.register(Depreciation)
class DepreciationAdmin(admin.ModelAdmin):
    list_display = ['asset', 'year', 'month', 'monthly_depreciation', 'accumulated_depreciation', 'book_value']
    list_filter = ['year', 'month']

@admin.register(DepreciationValue)
class DepreciationValueAdmin(admin.ModelAdmin):
    list_display = ['category', 'method', 'useful_life', 'residual_percent', 'rate']
    list_filter = ['method']