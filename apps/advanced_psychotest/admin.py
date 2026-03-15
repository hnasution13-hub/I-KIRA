"""
apps/advanced_psychotest/admin.py

Django Admin untuk Advanced Psychometric Test Suite.
Memungkinkan HR/admin mengelola bank soal, sesi, dan hasil tanpa developer.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import AdvSoal, AdvSession, AdvAnswer, AdvResult, TEST_TYPE_CHOICES


# ─── SOAL BANK ───────────────────────────────────────────────────────────────

@admin.register(AdvSoal)
class AdvSoalAdmin(admin.ModelAdmin):
    list_display  = ('nomor', 'test_type_badge', 'tipe_soal', 'pertanyaan_preview',
                     'tingkat_kesulitan', 'aktif')
    list_filter   = ('test_type', 'tipe_soal', 'tingkat_kesulitan', 'aktif')
    search_fields = ('pertanyaan',)
    list_per_page = 30
    ordering      = ('test_type', 'nomor')

    fieldsets = (
        ('Identitas Soal', {
            'fields': ('test_type', 'tipe_soal', 'nomor', 'tingkat_kesulitan', 'aktif'),
        }),
        ('Pertanyaan', {
            'fields': ('pertanyaan',),
        }),
        ('Pilihan Jawaban', {
            'fields': ('opsi_a', 'opsi_b', 'opsi_c', 'opsi_d', 'opsi_e', 'jawaban_benar'),
            'description': 'Untuk soal pilihan ganda. Opsi E khusus Likert (Sangat Setuju).',
        }),
        ('Big Five (OCEAN)', {
            'fields': ('bigfive_dimensi', 'bigfive_reverse'),
            'classes': ('collapse',),
        }),
        ('SJT Scoring', {
            'fields': ('sjt_skor_a', 'sjt_skor_b', 'sjt_skor_c', 'sjt_skor_d'),
            'classes': ('collapse',),
        }),
    )

    def pertanyaan_preview(self, obj):
        return obj.pertanyaan[:80] + '...' if len(obj.pertanyaan) > 80 else obj.pertanyaan
    pertanyaan_preview.short_description = 'Pertanyaan'

    def test_type_badge(self, obj):
        colors = {
            'raven':    '#1976d2', 'cogspeed': '#f57c00',
            'bigfive':  '#388e3c', 'sjt':      '#c62828', 'cfit': '#00838f',
        }
        color = colors.get(obj.test_type, '#9e9e9e')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:12px;font-size:.8rem;">{}</span>',
            color, obj.get_test_type_display()
        )
    test_type_badge.short_description = 'Tipe Tes'
    test_type_badge.admin_order_field = 'test_type'

    actions = ['aktifkan_soal', 'nonaktifkan_soal']

    def aktifkan_soal(self, request, queryset):
        n = queryset.update(aktif=True)
        self.message_user(request, f'{n} soal diaktifkan.')
    aktifkan_soal.short_description = 'Aktifkan soal terpilih'

    def nonaktifkan_soal(self, request, queryset):
        n = queryset.update(aktif=False)
        self.message_user(request, f'{n} soal dinonaktifkan.')
    nonaktifkan_soal.short_description = 'Nonaktifkan soal terpilih'


# ─── SESI ────────────────────────────────────────────────────────────────────

class AdvAnswerInline(admin.TabularInline):
    model = AdvAnswer
    extra = 0
    readonly_fields = ('soal', 'jawaban', 'likert_val', 'sjt_ranking', 'answered_at', 'is_correct')
    can_delete = False

    def is_correct(self, obj):
        val = obj.is_correct
        if val is None:
            return '—'
        return '✓' if val else '✗'
    is_correct.short_description = 'Benar?'


@admin.register(AdvSession)
class AdvSessionAdmin(admin.ModelAdmin):
    list_display  = ('id', 'peserta_nama', 'paket_display', 'status_badge',
                     'tujuan', 'created_at', 'expired_at')
    list_filter   = ('status', 'tujuan', 'test_type')
    search_fields = ('candidate__nama', 'employee__nama', 'created_by')
    readonly_fields = ('token', 'created_at', 'started_at', 'completed_at', 'tipe_started_at')
    list_per_page  = 25
    ordering       = ('-created_at',)
    inlines        = [AdvAnswerInline]

    fieldsets = (
        ('Peserta', {
            'fields': ('candidate', 'employee', 'tujuan'),
        }),
        ('Paket Tes', {
            'fields': ('paket', 'test_type', 'durasi_per_tes', 'durasi_menit'),
        }),
        ('Status & Waktu', {
            'fields': ('status', 'token', 'expired_at',
                       'created_at', 'started_at', 'completed_at', 'tipe_started_at'),
        }),
        ('Meta', {
            'fields': ('created_by',),
            'classes': ('collapse',),
        }),
    )

    def peserta_nama(self, obj):
        return obj.get_peserta_nama()
    peserta_nama.short_description = 'Peserta'

    def paket_display(self, obj):
        tipe_labels = dict(TEST_TYPE_CHOICES)
        badges = []
        colors = {
            'raven': '#1976d2', 'cogspeed': '#f57c00',
            'bigfive': '#388e3c', 'sjt': '#c62828', 'cfit': '#00838f',
        }
        for t in obj.get_paket():
            c = colors.get(t, '#9e9e9e')
            badges.append(
                f'<span style="background:{c};color:#fff;padding:1px 6px;'
                f'border-radius:10px;font-size:.75rem;margin-right:2px;">'
                f'{tipe_labels.get(t, t)}</span>'
            )
        return format_html(''.join(badges))
    paket_display.short_description = 'Paket Tes'

    def status_badge(self, obj):
        color = {
            'pending':   '#9e9e9e', 'started':   '#f57c00',
            'completed': '#388e3c', 'expired':   '#c62828',
        }.get(obj.status, '#9e9e9e')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:12px;font-size:.8rem;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'


# ─── HASIL ───────────────────────────────────────────────────────────────────

@admin.register(AdvResult)
class AdvResultAdmin(admin.ModelAdmin):
    list_display  = ('id', 'peserta_nama', 'test_type_badge', 'skor_total',
                     'grade_badge', 'percentile', 'created_at')
    list_filter   = ('test_type', 'grade')
    search_fields = ('candidate__nama', 'employee__nama')
    readonly_fields = ('created_at',)
    list_per_page  = 25
    ordering       = ('-created_at',)

    fieldsets = (
        ('Peserta & Tes', {
            'fields': ('session', 'candidate', 'employee', 'test_type'),
        }),
        ('Skor', {
            'fields': ('skor_total', 'grade', 'percentile'),
        }),
        ('Big Five OCEAN', {
            'fields': ('ocean_o', 'ocean_c', 'ocean_e', 'ocean_a', 'ocean_n'),
            'classes': ('collapse',),
        }),
        ('Detail & Catatan', {
            'fields': ('detail', 'interpretasi', 'catatan_hr'),
            'classes': ('collapse',),
        }),
        ('Meta', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def peserta_nama(self, obj):
        if obj.candidate:
            return obj.candidate.nama
        if obj.employee:
            return obj.employee.nama
        return '—'
    peserta_nama.short_description = 'Peserta'

    def test_type_badge(self, obj):
        colors = {
            'raven': '#1976d2', 'cogspeed': '#f57c00',
            'bigfive': '#388e3c', 'sjt': '#c62828', 'cfit': '#00838f',
        }
        color = colors.get(obj.test_type, '#9e9e9e')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:12px;font-size:.8rem;">{}</span>',
            color, obj.get_test_type_display()
        )
    test_type_badge.short_description = 'Tipe Tes'

    def grade_badge(self, obj):
        color = {
            'A': '#388e3c', 'B': '#1976d2', 'C': '#f57c00', 'D': '#e65100', 'E': '#c62828'
        }.get(obj.grade, '#9e9e9e')
        return format_html(
            '<strong style="color:{};">{}</strong>', color, obj.grade or '—'
        )
    grade_badge.short_description = 'Grade'
    grade_badge.admin_order_field = 'grade'
