from django.urls import path
from . import views
urlpatterns = [
    path('', views.contract_list, name='contract_list'),
    path('add/', views.contract_form, name='contract_add'),
    path('<int:pk>/', views.contract_detail, name='contract_detail'),
    path('<int:pk>/edit/', views.contract_form, name='contract_edit'),
    path('<int:pk>/delete/', views.contract_delete, name='contract_delete'),  # FIX P1
    path('<int:pk>/renew/', views.contract_renew, name='contract_renew'),       # P2.6
    path('<int:pk>/pkwt/', views.pkwt_print, name='pkwt_print'),               # Generate PKWT
    path('<int:pk>/pkwtt/', views.pkwtt_print, name='pkwtt_print'),            # Generate PKWTT
    path('<int:pk>/phl/', views.phl_print, name='phl_print'),                  # Generate PHL
    path('expiring/', views.contract_expiring, name='contract_expiring'),
    path('api/employee-info/', views.api_employee_info, name='contract_api_employee_info'),  # AJAX autofill
]
