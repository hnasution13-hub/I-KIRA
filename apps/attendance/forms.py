from django import forms
from .models import Attendance, Leave
from apps.employees.models import Employee


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'tanggal', 'check_in', 'check_out', 'status',
                  'keterlambatan', 'lembur_jam', 'keterangan']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'tanggal': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'check_in': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'check_out': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'keterlambatan': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'lembur_jam': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0}),
            'keterangan': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='Aktif').order_by('nama')


class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['employee', 'tipe_cuti', 'tanggal_mulai', 'tanggal_selesai',
                  'jumlah_hari', 'alasan', 'dokumen']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'tipe_cuti': forms.Select(attrs={'class': 'form-select'}),
            'tanggal_mulai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tanggal_selesai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'jumlah_hari': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'alasan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dokumen': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='Aktif').order_by('nama')

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('tanggal_mulai')
        end = cleaned_data.get('tanggal_selesai')
        if start and end and end < start:
            raise forms.ValidationError('Tanggal selesai tidak boleh sebelum tanggal mulai.')
        return cleaned_data


class OvertimeForm(forms.Form):
    """Form input lembur manual"""
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(status='Aktif'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Karyawan'
    )
    tanggal = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Tanggal Lembur'
    )
    jam_lembur = forms.DecimalField(
        max_digits=4, decimal_places=1, min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
        label='Jam Lembur'
    )
    keterangan = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Keterangan'
    )


class AttendanceFilterForm(forms.Form):
    BULAN_CHOICES = [(i, f'{i:02d}') for i in range(1, 13)]
    TAHUN_CHOICES = [(y, y) for y in range(2020, 2030)]

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(status='Aktif'),
        required=False,
        empty_label='Semua Karyawan',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    bulan = forms.ChoiceField(
        choices=BULAN_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    tahun = forms.ChoiceField(
        choices=TAHUN_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
