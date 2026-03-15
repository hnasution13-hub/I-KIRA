import django_filters
from django import forms
from .models import Asset, Category
from apps.employees.models import Employee
from apps.locations.models import Location
from apps.vendors.models import Vendor

class AssetFilter(django_filters.FilterSet):
    asset_name = django_filters.CharFilter(lookup_expr='icontains', label='Nama Asset')
    asset_code = django_filters.CharFilter(lookup_expr='icontains', label='Kode Asset')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    status = django_filters.ChoiceFilter(choices=Asset.STATUS_CHOICES)
    location = django_filters.ModelChoiceFilter(queryset=Location.objects.all())
    vendor = django_filters.ModelChoiceFilter(queryset=Vendor.objects.all())
    responsible = django_filters.ModelChoiceFilter(queryset=Employee.objects.all(), label='Penanggung Jawab')
    purchase_date_after = django_filters.DateFilter(field_name='purchase_date', lookup_expr='gte', widget=forms.DateInput(attrs={'type': 'date'}))
    purchase_date_before = django_filters.DateFilter(field_name='purchase_date', lookup_expr='lte', widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Asset
        fields = ['asset_name', 'asset_code', 'category', 'status', 'location', 'vendor', 'responsible']