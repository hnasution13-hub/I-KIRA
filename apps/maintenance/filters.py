import django_filters
from django import forms
from .models import Maintenance
from apps.assets.models import Asset

class MaintenanceFilter(django_filters.FilterSet):
    asset = django_filters.ModelChoiceFilter(queryset=Asset.objects.all())
    maintenance_type = django_filters.ChoiceFilter(choices=Maintenance.MAINTENANCE_TYPES)
    status = django_filters.ChoiceFilter(choices=Maintenance.STATUS_CHOICES)
    maintenance_date_after = django_filters.DateFilter(field_name='maintenance_date', lookup_expr='gte', widget=forms.DateInput(attrs={'type': 'date'}))
    maintenance_date_before = django_filters.DateFilter(field_name='maintenance_date', lookup_expr='lte', widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Maintenance
        fields = ['asset', 'maintenance_type', 'status']