from django import forms
from .models import Contract
from apps.employees.models import Employee


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = ['employee', 'tipe_kontrak', 'tanggal_mulai', 'tanggal_selesai',
                  'jabatan', 'departemen', 'gaji_pokok', 'status', 'file_kontrak', 'keterangan']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'tipe_kontrak': forms.Select(attrs={'class': 'form-select'}),
            'tanggal_mulai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tanggal_selesai': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'jabatan': forms.TextInput(attrs={'class': 'form-control'}),
            'departemen': forms.TextInput(attrs={'class': 'form-control'}),
            'gaji_pokok': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'file_kontrak': forms.FileInput(attrs={'class': 'form-control'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='Aktif').order_by('nama')
        self.fields['tanggal_selesai'].required = False

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('tanggal_mulai')
        end = cleaned_data.get('tanggal_selesai')
        tipe = cleaned_data.get('tipe_kontrak')
        if tipe in ['PKWT', 'Perjanjian Harian Lepas', 'Borongan'] and not end:
            raise forms.ValidationError(f'Tanggal selesai wajib diisi untuk kontrak {tipe}.')
        if start and end and end < start:
            raise forms.ValidationError('Tanggal selesai tidak boleh sebelum tanggal mulai.')
        return cleaned_data
