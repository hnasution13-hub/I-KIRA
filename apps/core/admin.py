from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Department, Position, AuditLog, Company, OrgChart, ApprovalMatrix


# ══════════════════════════════════════════════════════════════════════════════
#  COMPANY
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display  = [
        'nama', 'singkatan', 'slug', 'status_badge', 'paket',
        'kapasitas_display', 'enforce_limit',
        'pic_nama', 'tanggal_daftar', 'trial_sampai', 'sisa_hari', 'addon_summary',
    ]
    list_filter   = ['status', 'paket', 'enforce_limit', 'demo_reset_schedule']
    search_fields = ['nama', 'slug', 'email', 'pic_nama']
    prepopulated_fields = {'slug': ('nama',)}
    readonly_fields     = ['tanggal_daftar', 'last_demo_reset', 'created_at', 'updated_at']

    fieldsets = (
        ('Identitas Perusahaan', {
            'fields': ('nama', 'singkatan', 'slug', 'npwp', 'logo')
        }),
        ('Kontak', {
            'fields': ('alamat', 'no_telp', 'email', 'website'),
            'classes': ('collapse',)
        }),
        ('PIC Kontak', {
            'fields': ('pic_nama', 'pic_no_hp'),
        }),
        ('Paket & Kapasitas', {
            'fields': ('paket', 'enforce_limit', 'status', 'trial_sampai', 'catatan'),
            'description': 'Set paket tenant. enforce_limit=OFF berarti unlimited (untuk testing/demo).',
        }),
        ('Demo Config', {
            'fields': ('demo_reset_schedule', 'last_demo_reset'),
            'classes': ('collapse',),
            'description': 'Konfigurasi reset otomatis khusus akun Demo.',
        }),
        ('Aktivasi Add-On', {
            'fields': (
                'addon_assets', 'addon_recruitment', 'addon_psychotest',
                'addon_advanced_psychotest', 'addon_od', 'addon_performance',
            ),
        }),
        ('Penandatangan Default', {
            'fields': ('nama_penandatangan_default', 'jabatan_penandatangan_default'),
            'classes': ('collapse',)
        }),
        ('Info Sistem', {
            'fields': ('tanggal_daftar', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['action_reset_demo', 'action_extend_trial_30', 'action_activate', 'action_suspend']

    @admin.display(description='Status')
    def status_badge(self, obj):
        color = {
            'aktif':    '#16a34a',
            'trial':    '#2563eb',
            'demo':     '#ea580c',
            'suspend':  '#dc2626',
            'nonaktif': '#6b7280',
        }.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:11px">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description='Sisa Trial')
    def sisa_hari(self, obj):
        if obj.status == 'trial' and obj.trial_sampai:
            sisa = obj.trial_sisa_hari
            if sisa == 0:
                return format_html('<span style="color:red;font-weight:bold">EXPIRED</span>')
            color = 'red' if sisa <= 3 else ('orange' if sisa <= 7 else 'green')
            return format_html('<span style="color:{}">{} hari</span>', color, sisa)
        if obj.status == 'demo':
            return format_html('<span style="color:#ea580c">Demo</span>')
        return '-'

    @admin.display(description='Add-On Aktif')
    @admin.display(description='Kapasitas Karyawan')
    def kapasitas_display(self, obj):
        from django.utils.html import format_html
        if not obj.enforce_limit:
            return format_html('<span style="color:#888;font-size:11px">Unlimited</span>')
        jml  = obj.jumlah_karyawan_aktif
        limit = obj.paket_limit_karyawan
        pct   = obj.persen_kapasitas
        notif = obj.notif_kapasitas
        color = {'warning': '#f59e0b', 'critical': '#ef4444', 'full': '#dc2626'}.get(notif, '#22c55e')
        return format_html(
            '<span style="color:{};font-size:12px;font-weight:500">{}/{}</span>'
            '<span style="color:#888;font-size:10px"> ({}%)</span>',
            color, jml, limit, pct
        )

    def addon_summary(self, obj):
        addons = {
            'Assets':    obj.addon_assets,
            'Rekrutmen': obj.addon_recruitment,
            'Psikotes':  obj.addon_psychotest,
            'OCEAN':     obj.addon_advanced_psychotest,
            'OD':        obj.addon_od,
            'KPI':       getattr(obj, 'addon_performance', False),
        }
        badges = []
        for label, aktif in addons.items():
            color = '#16a34a' if aktif else '#d1d5db'
            badges.append(
                f'<span style="background:{color};color:{"#fff" if aktif else "#999"};'
                f'padding:2px 7px;border-radius:10px;font-size:11px;margin:1px;'
                f'display:inline-block">{label}</span>'
            )
        return format_html(' '.join(badges))

    @admin.action(description='🔄 Reset data demo sekarang')
    def action_reset_demo(self, request, queryset):
        from apps.registration.demo_seed import full_reset_and_seed
        count = 0
        for company in queryset.filter(status='demo'):
            try:
                full_reset_and_seed(company)
                count += 1
            except Exception as e:
                self.message_user(request, f'Error reset {company.nama}: {e}', level='error')
        self.message_user(request, f'{count} akun demo berhasil direset.')

    @admin.action(description='➕ Extend trial +30 hari')
    def action_extend_trial_30(self, request, queryset):
        from django.utils import timezone
        count = 0
        for company in queryset.filter(status='trial'):
            base = max(company.trial_sampai or timezone.now().date(), timezone.now().date())
            company.trial_sampai = base + timezone.timedelta(days=30)
            company.save(update_fields=['trial_sampai'])
            count += 1
        self.message_user(request, f'{count} trial diperpanjang +30 hari.')

    @admin.action(description='✅ Aktifkan (ubah ke Aktif)')
    def action_activate(self, request, queryset):
        queryset.update(status='aktif')
        self.message_user(request, f'{queryset.count()} company diaktifkan.')

    @admin.action(description='🚫 Suspend')
    def action_suspend(self, request, queryset):
        queryset.update(status='suspend')
        self.message_user(request, f'{queryset.count()} company disuspend.')


# ══════════════════════════════════════════════════════════════════════════════
#  DEPARTMENT
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display  = ['company', 'nama', 'kode', 'aktif']
    list_filter   = ['company', 'aktif']
    search_fields = ['nama']


# ══════════════════════════════════════════════════════════════════════════════
#  POSITION — tampilkan hierarki parent
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display  = ['company', 'nama', 'level', 'department', 'parent_display', 'aktif']
    list_filter   = ['company', 'level', 'department']
    search_fields = ['nama']
    autocomplete_fields = ['parent', 'department']
    raw_id_fields = ['parent']

    fieldsets = (
        ('Identitas Jabatan', {
            'fields': ('company', 'nama', 'level', 'department', 'parent', 'aktif', 'deskripsi')
        }),
        ('Job Description & Kualifikasi', {
            'fields': ('job_desc', 'skill_wajib', 'skill_diinginkan',
                       'pendidikan_min', 'pengalaman_min'),
            'classes': ('collapse',)
        }),
        ('Bobot ATS (total harus 100%)', {
            'fields': ('bobot_skill_wajib', 'bobot_pengalaman',
                       'bobot_pendidikan', 'bobot_skill_tambahan'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Atasan Jabatan')
    def parent_display(self, obj):
        if obj.parent:
            return f'↑ {obj.parent.nama}'
        return '— (puncak)'


# ══════════════════════════════════════════════════════════════════════════════
#  ORG CHART
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(OrgChart)
class OrgChartAdmin(admin.ModelAdmin):
    list_display  = ['company', 'nama', 'periode', 'berlaku_mulai', 'berlaku_sampai', 'status']
    list_filter   = ['company', 'status']
    search_fields = ['nama', 'periode']
    readonly_fields = ['created_at', 'updated_at']


# ══════════════════════════════════════════════════════════════════════════════
#  APPROVAL MATRIX
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(ApprovalMatrix)
class ApprovalMatrixAdmin(admin.ModelAdmin):
    list_display  = ['company', 'modul', 'jabatan_pemohon', 'level_approval',
                     'approver_display', 'auto_approve_hari', 'aktif']
    list_filter   = ['company', 'modul', 'aktif']
    search_fields = ['jabatan_pemohon__nama', 'jabatan_approver__nama']
    autocomplete_fields = ['jabatan_pemohon', 'jabatan_approver']

    @admin.display(description='Approver')
    def approver_display(self, obj):
        if obj.jabatan_approver:
            return obj.jabatan_approver.nama
        return format_html('<span style="color:#888">↑ auto (dari hierarki)</span>')


# ══════════════════════════════════════════════════════════════════════════════
#  USER
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'get_full_name', 'company', 'role', 'is_active', 'is_superuser']
    list_filter  = ['company', 'role', 'is_active', 'is_superuser']
    fieldsets    = BaseUserAdmin.fieldsets + (
        ('Info Tambahan', {
            'fields': ('company', 'nik', 'role', 'department', 'jabatan', 'no_hp', 'foto')
        }),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  AUDIT LOG
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display    = ['company', 'user', 'action', 'model_name', 'timestamp']
    list_filter     = ['company', 'action']
    readonly_fields = ['company', 'user', 'action', 'model_name', 'object_id',
                       'detail', 'ip_address', 'timestamp']
    ordering        = ['-timestamp']

    def has_add_permission(self, request):
        return False
