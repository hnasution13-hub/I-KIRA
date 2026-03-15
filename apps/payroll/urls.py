from django.urls import path
from . import views
urlpatterns = [
    path('salary/', views.salary_list, name='salary_list'),
    path('salary/add/', views.salary_form, name='salary_add'),
    path('salary/<int:employee_id>/edit/', views.salary_form, name='salary_edit'),
    path('salary/export/', views.export_salary, name='export_salary'),
    path('salary/import/', views.import_salary, name='import_salary'),
    path('salary/template/', views.download_template_salary, name='template_salary'),
    path('site-summary/', views.payroll_site_summary, name='payroll_site_summary'),
    path('site-allowance/', views.site_allowance_list, name='site_allowance_list'),
    path('site-allowance/add/', views.site_allowance_form, name='site_allowance_add'),
    path('site-allowance/<int:pk>/edit/', views.site_allowance_form, name='site_allowance_edit'),
    path('site-allowance/<int:pk>/delete/', views.site_allowance_delete, name='site_allowance_delete'),
    path('', views.payroll_list, name='payroll_list'),
    path('generate/', views.payroll_generate, name='payroll_generate'),
    path('<int:pk>/', views.payroll_detail, name='payroll_detail'),
    path('<int:pk>/export/excel/', views.export_payroll_rekap_excel, name='export_payroll_rekap_excel'),
    path('slip/<int:detail_pk>/', views.payslip, name='payslip'),
]
