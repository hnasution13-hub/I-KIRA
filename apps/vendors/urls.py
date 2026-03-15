from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.VendorListView.as_view(), name='vendor_list'),
    path('vendor/<int:pk>/', views.VendorDetailView.as_view(), name='vendor_detail'),
    path('vendor/create/', views.VendorCreateView.as_view(), name='vendor_create'),
    path('vendor/<int:pk>/update/', views.VendorUpdateView.as_view(), name='vendor_update'),
    path('vendor/<int:pk>/delete/', views.VendorDeleteView.as_view(), name='vendor_delete'),
]