from django import forms

from apps.employees.models import Employee
from apps.employees.models import Employee
from apps.locations.models import Location
from .models import Movement, Assignment

class MovementForm(forms.ModelForm):
    class Meta:
        model = Movement
        fields = '__all__'
        widgets = {
            'movement_date': forms.DateInput(attrs={'type': 'date'}),
            'document_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter pilihan untuk from_pic, to_pic, from_location, to_location
        self.fields['from_pic'].queryset = Employee.objects.filter(status='Aktif')
        self.fields['to_pic'].queryset = Employee.objects.filter(status='Aktif')
        self.fields['from_location'].queryset = Location.objects.all()
        self.fields['to_location'].queryset = Location.objects.all()


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = '__all__'
        widgets = {
            'assignment_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_return_date': forms.DateInput(attrs={'type': 'date'}),
        }