from django.contrib import admin
from .models import Violation, Severance


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'tipe_pelanggaran', 'tanggal_kejadian', 'tingkat', 'status']
    list_filter   = ['tingkat', 'status', 'tipe_pelanggaran']
    search_fields = ['employee__nama', 'employee__nik']


@admin.register(Severance)
class SeveranceAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'tanggal_phk', 'alasan_phk', 'dasar_pasal',
                     'pesangon', 'upmk', 'uang_pisah', 'kompensasi_pkwt', 'total_pesangon']
    list_filter   = ['alasan_phk', 'dasar_pasal']
    search_fields = ['employee__nama', 'employee__nik']
    readonly_fields = ['masa_kerja_tahun', 'masa_kerja_bulan', 'total_upah',
                       'pengali_pesangon', 'pesangon', 'upmk', 'uang_pisah',
                       'kompensasi_pkwt', 'total_pesangon']
