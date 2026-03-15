from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    path('',          views.register_landing, name='landing'),
    path('demo/',     views.register_demo,    name='demo'),
    path('trial/',    views.register_trial,   name='trial'),
    path('sukses/',   views.register_success, name='success'),
    path('upgrade/',  views.upgrade_page,     name='upgrade'),
]
