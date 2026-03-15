from django import forms
from .models import Location

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_code(self):
        code = self.cleaned_data['code']
        if Location.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Kode lokasi sudah digunakan.")
        return code