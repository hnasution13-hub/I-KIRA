from django import forms
from .models import Employee, EmployeeDocument
from apps.core.models import Department, Position


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'nik', 'nama', 'department', 'jabatan', 'status_karyawan', 'join_date', 'status',
            'jenis_kelamin', 'tempat_lahir', 'tanggal_lahir', 'agama', 'pendidikan', 'alamat',
            'no_ktp', 'no_npwp', 'no_bpjs_kes', 'no_bpjs_tk',
            'email', 'no_hp', 'hp_darurat', 'nama_darurat',
            'nama_bank', 'no_rek', 'nama_rek', 'foto',
        ]
        widgets = {
            'nik': forms.TextInput(attrs={'class': 'form-control'}),
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'jabatan': forms.Select(attrs={'class': 'form-select'}),
            'status_karyawan': forms.Select(attrs={'class': 'form-select'}),
            'join_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'jenis_kelamin': forms.Select(attrs={'class': 'form-select'}),
            'tempat_lahir': forms.TextInput(attrs={'class': 'form-control'}),
            'tanggal_lahir': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'agama': forms.Select(attrs={'class': 'form-select'}),
            'pendidikan': forms.Select(attrs={'class': 'form-select'}),
            'alamat': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'no_ktp': forms.TextInput(attrs={'class': 'form-control'}),
            'no_npwp': forms.TextInput(attrs={'class': 'form-control'}),
            'no_bpjs_kes': forms.TextInput(attrs={'class': 'form-control'}),
            'no_bpjs_tk': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'no_hp': forms.TextInput(attrs={'class': 'form-control'}),
            'hp_darurat': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_darurat': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_bank': forms.TextInput(attrs={'class': 'form-control'}),
            'no_rek': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_rek': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(aktif=True)
        self.fields['jabatan'].queryset = Position.objects.filter(aktif=True)
        for field in ['department', 'jabatan', 'tanggal_lahir', 'foto']:
            self.fields[field].required = False


class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = ['tipe', 'nama_file', 'file', 'keterangan']
        widgets = {
            'tipe': forms.Select(attrs={'class': 'form-select'}),
            'nama_file': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'keterangan': forms.TextInput(attrs={'class': 'form-control'}),
        }
