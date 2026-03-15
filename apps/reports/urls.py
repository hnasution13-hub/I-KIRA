from django.urls import path
from . import views
urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('attendance/', views.report_attendance, name='report_attendance'),
    path('payroll/', views.report_payroll, name='report_payroll'),
    path('employee/', views.report_employee, name='report_employee'),
    path('contract/', views.report_contract, name='report_contract'),
    path('violation/', views.report_violation, name='report_violation'),
    path('recruitment/', views.report_recruitment, name='report_recruitment'),
    # Export Excel
    path('attendance/export/excel/', views.export_attendance_excel, name='export_attendance_excel'),
    path('employee/export/excel/', views.export_employee_excel, name='export_employee_excel'),
    path('payroll/export/excel/', views.export_payroll_excel, name='export_payroll_excel'),
    path('violation/export/excel/', views.export_violation_excel, name='export_violation_excel'),
    path('contract/export/excel/', views.export_contract_excel, name='export_contract_excel'),
    path('recruitment/export/excel/', views.export_recruitment_excel, name='export_recruitment_excel'),
]
