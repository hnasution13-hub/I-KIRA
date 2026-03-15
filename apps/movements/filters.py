import django_filters
from django import forms

from apps.locations.models import Location
from .models import Movement, Assignment
from apps.assets.models import Asset
from apps.employees.models import Employee

class MovementFilter(django_filters.FilterSet):
    asset = django_filters.ModelChoiceFilter(queryset=Asset.objects.all())
    movement_type = django_filters.ChoiceFilter(choices=Movement.MOVEMENT_TYPES)
    movement_date_after = django_filters.DateFilter(field_name='movement_date', lookup_expr='gte', widget=forms.DateInput(attrs={'type': 'date'}))
    movement_date_before = django_filters.DateFilter(field_name='movement_date', lookup_expr='lte', widget=forms.DateInput(attrs={'type': 'date'}))
    from_pic = django_filters.ModelChoiceFilter(queryset=Employee.objects.all())
    to_pic = django_filters.ModelChoiceFilter(queryset=Employee.objects.all())

    class Meta:
        model = Movement
        fields = ['asset', 'movement_type', 'from_pic', 'to_pic']


class AssignmentFilter(django_filters.FilterSet):
    asset = django_filters.ModelChoiceFilter(queryset=Asset.objects.all())
    current_pic = django_filters.ModelChoiceFilter(queryset=Employee.objects.all())
    current_location = django_filters.ModelChoiceFilter(queryset=Location.objects.all())

    class Meta:
        model = Assignment
        fields = ['asset', 'current_pic', 'current_location']