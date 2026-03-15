from django.contrib import admin
from .models import ManpowerRequest, Candidate, OfferingLetter

@admin.register(ManpowerRequest)
class ManpowerRequestAdmin(admin.ModelAdmin):
    list_display = ['nomor_mprf', 'department', 'nama_jabatan', 'tipe', 'jumlah_kebutuhan', 'status', 'target_date']
    list_filter = ['status', 'tipe', 'department']
    search_fields = ['nomor_mprf', 'nama_jabatan']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['nama', 'jabatan_dilamar', 'sumber', 'tanggal_melamar', 'status']
    list_filter = ['status', 'pendidikan']
    search_fields = ['nama', 'email', 'jabatan_dilamar']

@admin.register(OfferingLetter)
class OfferingLetterAdmin(admin.ModelAdmin):
    list_display = ['nomor', 'candidate', 'jabatan', 'tanggal_surat', 'gaji_pokok', 'status']
    list_filter = ['status']
    search_fields = ['nomor', 'candidate__nama']
