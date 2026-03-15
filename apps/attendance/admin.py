from django.contrib import admin
from .models import Attendance, Leave, Holiday

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['nama', 'tanggal', 'keterangan']
    ordering = ['tanggal']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'tanggal', 'check_in', 'check_out', 'status', 'keterlambatan', 'lembur_jam']
    list_filter = ['status', 'tanggal']
    search_fields = ['employee__nama', 'employee__nik']
    date_hierarchy = 'tanggal'

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['employee', 'tipe_cuti', 'tanggal_mulai', 'tanggal_selesai', 'jumlah_hari', 'status']
    list_filter = ['status', 'tipe_cuti']
    search_fields = ['employee__nama']
