from django.contrib import admin
from .models import Contract

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['nomor_kontrak', 'employee', 'tipe_kontrak', 'tanggal_mulai', 'tanggal_selesai', 'status']
    list_filter = ['status', 'tipe_kontrak']
    search_fields = ['nomor_kontrak', 'employee__nama']
    ordering = ['-tanggal_mulai']
