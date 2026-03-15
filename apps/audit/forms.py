from django import forms
from .models import AuditLog

class AuditLogFilterForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    username = forms.CharField(required=False)
    action = forms.ChoiceField(required=False, choices=[('', 'Semua')] + AuditLog.ACTION_CHOICES)