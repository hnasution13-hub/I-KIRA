from django.contrib import admin
from .models import Provinsi, Kabupaten, Kecamatan, Kelurahan


@admin.register(Provinsi)
class ProvinsiAdmin(admin.ModelAdmin):
    list_display = ['kode', 'nama']
    search_fields = ['nama', 'kode']


@admin.register(Kabupaten)
class KabupatenAdmin(admin.ModelAdmin):
    list_display = ['kode', 'nama', 'provinsi']
    list_filter = ['provinsi']
    search_fields = ['nama', 'kode']


@admin.register(Kecamatan)
class KecamatanAdmin(admin.ModelAdmin):
    list_display = ['kode', 'nama', 'kabupaten']
    list_filter = ['kabupaten__provinsi']
    search_fields = ['nama', 'kode']


@admin.register(Kelurahan)
class KelurahanAdmin(admin.ModelAdmin):
    list_display = ['kode', 'nama', 'kecamatan', 'kode_pos']
    list_filter = ['kecamatan__kabupaten__provinsi']
    search_fields = ['nama', 'kode', 'kode_pos']


from .models import Bank

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display  = ['kode', 'nama']
    search_fields = ['nama', 'kode']
