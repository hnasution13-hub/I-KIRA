import django_filters
from .models import Location

class LocationFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.ChoiceFilter(choices=Location.TYPE_CHOICES)

    class Meta:
        model = Location
        fields = ['name', 'code', 'type']