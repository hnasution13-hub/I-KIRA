from django import forms
from .models import Violation, Severance
from apps.employees.models import Employee


class ViolationForm(forms.ModelForm):
    class Meta:
        model = Violation
        fields = ['employee', 'tipe_pelanggaran', 'tanggal_kejadian', 'deskripsi',
                  'tingkat', 'poin', 'sanksi', 'dokumen', 'status']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'tipe_pelanggaran': forms.Select(attrs={'class': 'form-select'}),
            'tanggal_kejadian': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'tingkat': forms.Select(attrs={'class': 'form-select'}),
            'poin': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'sanksi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dokumen': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='Aktif').order_by('nama')
        self.fields['dokumen'].required = False


class SeveranceCalculatorForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(status='Aktif'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Karyawan'
    )
    tanggal_phk = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Tanggal PHK'
    )
    alasan_phk = forms.ChoiceField(
        choices=Severance.ALASAN_PHK_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Alasan PHK'
    )
    gaji_pokok = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Gaji Pokok'
    )
    tunjangan_tetap = forms.IntegerField(
        min_value=0, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Total Tunjangan Tetap'
    )
