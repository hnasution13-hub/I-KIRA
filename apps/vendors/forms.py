from django import forms
from .models import Vendor

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_code(self):
        code = self.cleaned_data['code']
        if Vendor.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Kode vendor sudah digunakan.")
        return code