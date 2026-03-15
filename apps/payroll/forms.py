from django import forms
from .models import SalaryBenefit, Payroll
from apps.employees.models import Employee
import datetime  # FIX BUG-010: import di level modul, bukan di dalam body class


class SalaryBenefitForm(forms.ModelForm):
    class Meta:
        model = SalaryBenefit
        fields = [
            'gaji_pokok', 'tunjangan_transport', 'tunjangan_makan',
            'tunjangan_komunikasi', 'tunjangan_kesehatan', 'tunjangan_jabatan',
            'tunjangan_keahlian', 'bonus_tahunan', 'thr',
        ]
        widgets = {f: forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
                   for f in ['gaji_pokok', 'tunjangan_transport', 'tunjangan_makan',
                              'tunjangan_komunikasi', 'tunjangan_kesehatan', 'tunjangan_jabatan',
                              'tunjangan_keahlian', 'bonus_tahunan', 'thr']}


class PayrollGenerateForm(forms.Form):
    BULAN_CHOICES = [
        (1, 'Januari'), (2, 'Februari'), (3, 'Maret'), (4, 'April'),
        (5, 'Mei'), (6, 'Juni'), (7, 'Juli'), (8, 'Agustus'),
        (9, 'September'), (10, 'Oktober'), (11, 'November'), (12, 'Desember'),
    ]
    # FIX BUG-010: import datetime sudah dipindah ke atas file
    TAHUN_CHOICES = [(y, y) for y in range(2020, datetime.date.today().year + 2)]

    bulan = forms.ChoiceField(
        choices=BULAN_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tahun = forms.ChoiceField(
        choices=TAHUN_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='Semua Departemen',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.core.models import Department
        self.fields['department'].queryset = Department.objects.filter(aktif=True)

    def get_periode(self):
        bulan = int(self.cleaned_data['bulan'])
        tahun = int(self.cleaned_data['tahun'])
        return f"{tahun}-{bulan:02d}"
