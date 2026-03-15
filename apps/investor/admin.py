from django.contrib import admin
from .models import InvestorPool, InvestorAccount, PayoutHistory, Milestone, RevenueEntry


@admin.register(InvestorPool)
class InvestorPoolAdmin(admin.ModelAdmin):
    list_display  = ['nama', 'total_dana', 'modal_founder', 'total_investor_pool_display', 'persen_investor', 'target_return_x']
    readonly_fields = ['total_investor_pool_display']

    def total_investor_pool_display(self, obj):
        return f'Rp {obj.total_investor_pool:,.0f}'
    total_investor_pool_display.short_description = 'Total Investor Pool'


@admin.register(InvestorAccount)
class InvestorAccountAdmin(admin.ModelAdmin):
    list_display  = ['nama', 'username', 'modal_investasi', 'porsi_persen_display',
                     'total_diterima', 'target_return_display', 'progress_display', 'aktif']
    list_filter   = ['aktif', 'pool']
    readonly_fields = ['last_login', 'created_at', 'porsi_persen_display',
                       'target_return_display', 'sisa_target_display', 'progress_display']
    fieldsets = (
        ('Akun', {'fields': ('pool', 'nama', 'username', 'password', 'aktif')}),
        ('Data Investasi', {'fields': ('modal_investasi', 'tanggal_mulai')}),
        ('Perhitungan (otomatis)', {'fields': (
            'porsi_persen_display', 'target_return_display',
            'total_diterima', 'sisa_target_display', 'progress_display'
        )}),
        ('Catatan Founder (tidak terlihat investor)', {'fields': ('catatan_founder',)}),
        ('Info', {'fields': ('created_at', 'last_login')}),
    )

    def porsi_persen_display(self, obj):
        return f'{obj.porsi_persen}%'
    porsi_persen_display.short_description = 'Porsi dari Pool'

    def target_return_display(self, obj):
        return f'Rp {obj.target_total_return:,.0f}'
    target_return_display.short_description = 'Target Return'

    def sisa_target_display(self, obj):
        return f'Rp {obj.sisa_target:,.0f}'
    sisa_target_display.short_description = 'Sisa Target'

    def progress_display(self, obj):
        return f'{obj.progress_persen:.1f}%'
    progress_display.short_description = 'Progress'

    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)


@admin.register(PayoutHistory)
class PayoutHistoryAdmin(admin.ModelAdmin):
    list_display = ['investor', 'bulan', 'jumlah', 'keterangan']
    list_filter  = ['investor', 'bulan']
    ordering     = ['-bulan']


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['judul', 'status', 'target_date', 'urutan']
    list_filter  = ['status']
    ordering     = ['urutan']


@admin.register(RevenueEntry)
class RevenueEntryAdmin(admin.ModelAdmin):
    list_display = ['bulan', 'mrr', 'biaya_ops', 'nett_display', 'client_baru']
    ordering     = ['-bulan']

    def nett_display(self, obj):
        return f'Rp {obj.nett:,.0f}'
    nett_display.short_description = 'Nett'
