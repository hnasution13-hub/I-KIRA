from django.urls import path
from . import views

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('add/', views.employee_form, name='employee_add'),
    path('<int:pk>/', views.employee_detail, name='employee_detail'),
    path('<int:pk>/edit/', views.employee_form, name='employee_edit'),
    path('<int:pk>/salary/', views.salary_form, name='employee_salary_form'),
    path('<int:pk>/deactivate/', views.employee_deactivate, name='employee_deactivate'),
    path('export/', views.export_karyawan, name='employee_export'),
    path('import/', views.import_karyawan, name='employee_import'),
    path('import/template/', views.download_template, name='employee_import_template'),
    # Manajemen akun portal
    path('accounts/', views.employee_accounts, name='employee_accounts'),
    path('accounts/bulk-create/', views.employee_account_bulk_create, name='employee_account_bulk_create'),
    path('<int:pk>/account/', views.employee_account_create, name='employee_account_action'),

    # Anti-Fraud — Daftarkan Perangkat
    path('<int:pk>/add-device/', views.employee_add_device, name='employee_add_device'),

    # API
    path('api/', views.api_employees, name='api_employees'),
    path('api/jabatan/', views.api_jabatan_by_dept, name='api_jabatan_by_dept'),
]
