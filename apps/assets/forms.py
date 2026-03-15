# ==================================================
# FILE: apps/assets/forms.py
# PATH: D:/Project Pyton/Asset Management Django/apps/assets/forms.py
# DESKRIPSI: Form untuk model Asset dan Category
# VERSION: 1.0.0
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from django import forms
from .models import Asset, Category
from apps.employees.models import Employee
from apps.vendors.models import Vendor

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = '__all__'
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warranty_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'cabinet': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Batasi pilihan hanya yang aktif
        self.fields['responsible'].queryset = Employee.objects.filter(status='Aktif')
        self.fields['vendor'].queryset = Vendor.objects.filter(status='Aktif')
        # Tambahkan class form-control ke semua field
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs['class'] = 'form-control'

    def clean_asset_code(self):
        code = self.cleaned_data['asset_code']
        # Validasi unik sudah otomatis oleh model, tapi bisa ditambahkan validasi format
        return code

    def clean(self):
        cleaned_data = super().clean()
        purchase_price = cleaned_data.get('purchase_price')
        residual_value = cleaned_data.get('residual_value')
        if residual_value and purchase_price and residual_value > purchase_price:
            raise forms.ValidationError("Nilai residu tidak boleh melebihi harga perolehan.")
        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'code', 'parent', 'asset_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'asset_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_code(self):
        code = self.cleaned_data['code']
        if Category.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Kode kategori sudah digunakan.")
        return code