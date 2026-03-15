from django.contrib import admin
from .models import Employee, EmployeeDocument, PointOfHire, JobSite, Perusahaan, AnakKaryawan, EmployeeDevice, PortalCheckInLog

@admin.register(Perusahaan)
class PerusahaanAdmin(admin.ModelAdmin):
    list_display  = ['nama', 'singkatan', 'pic_nama', 'pic_hp', 'aktif']
    list_filter   = ['aktif']
    search_fields = ['nama', 'singkatan', 'npwp']

@admin.register(PointOfHire)
class PointOfHireAdmin(admin.ModelAdmin):
    list_display = ['nama', 'aktif']
    list_filter  = ['aktif']

@admin.register(JobSite)
class JobSiteAdmin(admin.ModelAdmin):
    list_display = ['nama', 'aktif']
    list_filter  = ['aktif']

class AnakKaryawanInline(admin.TabularInline):
    model  = AnakKaryawan
    extra  = 1
    fields = ['urutan', 'nama', 'tgl_lahir', 'jenis_kelamin', 'no_bpjs_kes', 'tanggungan_bpjs']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['nik', 'nama', 'department', 'jabatan', 'status_karyawan', 'join_date', 'status']
    list_filter  = ['status', 'status_karyawan', 'department', 'jenis_kelamin']
    search_fields = ['nik', 'nama', 'email', 'no_ktp']
    ordering     = ['nama']
    date_hierarchy = 'join_date'
    inlines      = [AnakKaryawanInline]

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'tipe', 'nama_file', 'uploaded_at']
    list_filter = ['tipe']

@admin.register(EmployeeDevice)
class EmployeeDeviceAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'mac_address', 'nama_perangkat', 'platform', 'aktif', 'terdaftar_oleh', 'created_at', 'last_seen']
    list_filter   = ['aktif']
    search_fields = ['employee__nama', 'employee__nik', 'mac_address', 'nama_perangkat']
    list_editable = ['aktif']
    ordering      = ['-created_at']


@admin.register(PortalCheckInLog)
class PortalCheckInLogAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'tipe', 'waktu', 'device_dikenal', 'gps_valid', 'flagged', 'mac_address', 'ip_address']
    list_filter   = ['tipe', 'device_dikenal', 'gps_valid', 'flagged']
    search_fields = ['employee__nama', 'employee__nik', 'mac_address', 'ip_address']
    readonly_fields = ['employee', 'device', 'mac_address', 'latitude', 'longitude',
                       'akurasi_gps', 'ip_address', 'user_agent', 'tipe', 'waktu',
                       'device_dikenal', 'gps_valid', 'flagged', 'catatan_flag']
    ordering      = ['-waktu']

    def has_add_permission(self, request):
        return False  # Log tidak bisa dibuat manual
