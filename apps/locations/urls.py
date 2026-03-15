from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('', views.LocationListView.as_view(), name='location_list'),
    path('location/<int:pk>/', views.LocationDetailView.as_view(), name='location_detail'),
    path('location/create/', views.LocationCreateView.as_view(), name='location_create'),
    path('location/<int:pk>/update/', views.LocationUpdateView.as_view(), name='location_update'),
    path('location/<int:pk>/delete/', views.LocationDeleteView.as_view(), name='location_delete'),
    path('hierarchy/', views.LocationHierarchyView.as_view(), name='location_hierarchy'),
]