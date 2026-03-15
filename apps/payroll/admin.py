from django.contrib import admin
from .models import SalaryBenefit, Payroll, PayrollDetail

@admin.register(SalaryBenefit)
class SalaryBenefitAdmin(admin.ModelAdmin):
    list_display = ['employee', 'gaji_pokok', 'total_tunjangan', 'total_take_home_pay', 'updated_at']
    search_fields = ['employee__nama', 'employee__nik']

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['periode', 'jumlah_karyawan', 'total_gaji_bersih', 'status', 'tanggal_generate']
    list_filter = ['status']
    ordering = ['-periode']

@admin.register(PayrollDetail)
class PayrollDetailAdmin(admin.ModelAdmin):
    list_display = ['payroll', 'employee', 'gaji_pokok', 'gaji_bersih']
    list_filter = ['payroll']
    search_fields = ['employee__nama']
