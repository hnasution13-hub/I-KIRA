from django import forms
from apps.core.models import Department
import datetime


class ReportFilterForm(forms.Form):
    BULAN_CHOICES = [
        (1,'Januari'),(2,'Februari'),(3,'Maret'),(4,'April'),
        (5,'Mei'),(6,'Juni'),(7,'Juli'),(8,'Agustus'),
        (9,'September'),(10,'Oktober'),(11,'November'),(12,'Desember'),
    ]
    TAHUN_CHOICES = [(y,y) for y in range(2020, datetime.date.today().year+2)]

    bulan = forms.ChoiceField(
        choices=BULAN_CHOICES,
        initial=datetime.date.today().month,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    tahun = forms.ChoiceField(
        choices=TAHUN_CHOICES,
        initial=datetime.date.today().year,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(aktif=True),
        required=False,
        empty_label='Semua Departemen',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
