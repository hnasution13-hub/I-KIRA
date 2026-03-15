# ==================================================
# FILE: apps/custom_categories/forms.py
# PATH: D:/Project Pyton/Asset Management Django/apps/custom_categories/forms.py
# DESKRIPSI: Form untuk input custom kategori
# VERSION: 1.0.0
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from django import forms
from .models import CategoryCustom
from apps.assets.models import Category

class CategoryCustomForm(forms.ModelForm):
    category_level1 = forms.ModelChoiceField(
        queryset=Category.objects.filter(parent__isnull=True),
        required=True,
        label="Kategori Utama",
        empty_label="Pilih Kategori",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    category_level2 = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        label="Sub Kategori",
        empty_label="Pilih Sub Kategori",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    category_level3 = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False,
        label="Tipe Asset",
        empty_label="Pilih Tipe Asset",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CategoryCustom
        fields = ['custom_field', 'asset_name', 'tag_number']
        widgets = {
            'custom_field': forms.TextInput(attrs={'class': 'form-control'}),
            'asset_name': forms.TextInput(attrs={'class': 'form-control'}),
            'tag_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'category_level1' in self.data:
            try:
                cat1_id = int(self.data.get('category_level1'))
                self.fields['category_level2'].queryset = Category.objects.filter(parent_id=cat1_id)
            except (ValueError, TypeError):
                pass
        if 'category_level2' in self.data:
            try:
                cat2_id = int(self.data.get('category_level2'))
                self.fields['category_level3'].queryset = Category.objects.filter(parent_id=cat2_id)
            except (ValueError, TypeError):
                pass
        # Jika instance sudah ada (edit), set nilai awal dropdown
        if self.instance.pk:
            cat = self.instance.category
            # Cari level1, level2, level3
            ancestors = []
            while cat:
                ancestors.insert(0, cat)
                cat = cat.parent
            if len(ancestors) >= 1:
                self.fields['category_level1'].initial = ancestors[0]
                self.fields['category_level1'].queryset = Category.objects.filter(parent__isnull=True)
            if len(ancestors) >= 2:
                self.fields['category_level2'].initial = ancestors[1]
                self.fields['category_level2'].queryset = Category.objects.filter(parent_id=ancestors[0].id)
            if len(ancestors) >= 3:
                self.fields['category_level3'].initial = ancestors[2]
                self.fields['category_level3'].queryset = Category.objects.filter(parent_id=ancestors[1].id)