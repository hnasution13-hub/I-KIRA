from django import forms
from .models import ManpowerRequest, Candidate, OfferingLetter, OfferingTemplate
from apps.core.models import Department, Position


class ManpowerRequestForm(forms.ModelForm):
    class Meta:
        model = ManpowerRequest
        fields = ['department', 'jabatan', 'nama_jabatan', 'tipe', 'jumlah_kebutuhan',
                  'alasan', 'kualifikasi', 'target_date', 'status']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'jabatan': forms.Select(attrs={'class': 'form-select'}),
            'nama_jabatan': forms.TextInput(attrs={'class': 'form-control'}),
            'tipe': forms.Select(attrs={'class': 'form-select'}),
            'jumlah_kebutuhan': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'alasan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'kualifikasi': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(aktif=True)
        self.fields['jabatan'].queryset = Position.objects.filter(aktif=True)
        self.fields['jabatan'].required = False


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['mprf', 'nama', 'email', 'no_hp', 'jabatan_dilamar', 'sumber',
                  'status', 'pendidikan', 'pengalaman_tahun', 'ekspektasi_gaji',
                  'cv_file', 'catatan']
        widgets = {
            'mprf': forms.Select(attrs={'class': 'form-select'}),
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'no_hp': forms.TextInput(attrs={'class': 'form-control'}),
            'jabatan_dilamar': forms.TextInput(attrs={'class': 'form-control'}),
            'sumber': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'JobStreet, Referral, Walk-in...'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'pendidikan': forms.Select(attrs={'class': 'form-select'}),
            'pengalaman_tahun': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'ekspektasi_gaji': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'cv_file': forms.FileInput(attrs={'class': 'form-control'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mprf'].queryset = ManpowerRequest.objects.filter(
            status__in=['Open', 'In Process']
        )
        self.fields['mprf'].required = False
        self.fields['ekspektasi_gaji'].required = False
        self.fields['cv_file'].required = False


class OfferingLetterForm(forms.ModelForm):
    class Meta:
        model = OfferingLetter
        fields = [
            'candidate', 'template', 'jabatan', 'department',
            'tanggal_surat', 'tanggal_mulai_kerja',
            'site_lokasi', 'lokasi_kerja', 'point_of_hire', 'join_date_text',
            'gaji_pokok', 'fixed_allowance', 'tunjangan_total',
            'masa_probasi', 'no_arsip', 'status', 'keterangan',
        ]
        widgets = {
            'candidate':           forms.Select(attrs={'class': 'form-select'}),
            'template':            forms.Select(attrs={'class': 'form-select'}),
            'jabatan':             forms.TextInput(attrs={'class': 'form-control'}),
            'department':          forms.Select(attrs={'class': 'form-select'}),
            'tanggal_surat':       forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tanggal_mulai_kerja': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'site_lokasi':         forms.TextInput(attrs={'class': 'form-control'}),
            'lokasi_kerja':        forms.TextInput(attrs={'class': 'form-control'}),
            'point_of_hire':       forms.TextInput(attrs={'class': 'form-control'}),
            'join_date_text':      forms.TextInput(attrs={'class': 'form-control'}),
            'gaji_pokok':          forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'fixed_allowance':     forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'tunjangan_total':     forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'masa_probasi':        forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'no_arsip':            forms.TextInput(attrs={'class': 'form-control'}),
            'status':              forms.Select(attrs={'class': 'form-select'}),
            'keterangan':          forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['candidate'].queryset = Candidate.objects.exclude(
            status__in=['Hired', 'Rejected', 'Withdrawn']
        )
        self.fields['template'].queryset = OfferingTemplate.objects.all()
        self.fields['department'].queryset = Department.objects.filter(aktif=True)
        self.fields['department'].required  = False
        self.fields['template'].required    = False
        self.fields['site_lokasi'].required = False
        self.fields['lokasi_kerja'].required = False
        self.fields['point_of_hire'].required = False
        self.fields['no_arsip'].required    = False
