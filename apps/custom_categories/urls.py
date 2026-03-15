# ==================================================
# FILE: apps/custom_categories/urls.py
# PATH: D:/Project Pyton/Asset Management Django/apps/custom_categories/urls.py
# DESKRIPSI: URL routing untuk custom kategori
# VERSION: 1.0.0
# UPDATE TERAKHIR: 05/03/2026
# ==================================================

from django.urls import path
from . import views

app_name = 'custom_categories'

urlpatterns = [
    path('', views.CategoryCustomListView.as_view(), name='list'),
    path('add/', views.CategoryCustomCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.CategoryCustomUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.CategoryCustomDeleteView.as_view(), name='delete'),
    path('ajax/load-subcategories/', views.load_subcategories, name='load_subcategories'),
]