from django.urls import path
from . import views

app_name = 'investor'

urlpatterns = [
    path('',           views.investor_login,      name='login'),
    path('logout/',    views.investor_logout,      name='logout'),
    path('home/',      views.investor_dashboard,   name='dashboard'),
    path('profil/',    views.investor_profil,      name='profil'),
    path('api/stats/', views.investor_api_stats,   name='api_stats'),
    path('api/profil/',views.investor_api_profil,  name='api_profil'),
]
