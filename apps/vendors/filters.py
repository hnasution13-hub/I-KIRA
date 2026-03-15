import django_filters
from .models import Vendor

class VendorFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Vendor._meta.get_field('status').choices)

    class Meta:
        model = Vendor
        fields = ['name', 'code', 'status']