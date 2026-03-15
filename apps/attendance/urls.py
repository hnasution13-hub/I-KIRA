from django.urls import path
from . import views
from .import_absensi import attendance_import, attendance_import_process, download_template_absensi

urlpatterns = [
    path('', views.attendance_list, name='attendance_list'),
    path('check-in/', views.check_in, name='check_in'),
    path('leave/', views.leave_list, name='leave_list'),
    path('leave/add/', views.leave_form, name='leave_add'),
    path('leave/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leave/<int:pk>/reject/', views.leave_reject, name='leave_reject'),
    path('leave/<int:pk>/', views.leave_detail, name='leave_detail'),
    path('overtime/<int:pk>/approve/', views.overtime_approve, name='overtime_approve'),
    path('overtime/<int:pk>/reject/', views.overtime_reject, name='overtime_reject'),
    path('report/', views.attendance_report, name='attendance_report'),
    path('calendar/', views.attendance_calendar, name='attendance_calendar'),
    path('overtime/', views.overtime_list, name='overtime_list'),
    path('overtime/recalculate/', views.overtime_recalculate, name='overtime_recalculate'),
    path('overtime/add/', views.overtime_form, name='overtime_add'),
    path('overtime/<int:pk>/edit/', views.overtime_form, name='overtime_edit'),
    path('bulk/', views.attendance_bulk, name='attendance_bulk'),
    # Import fingerprint
    path('import/', attendance_import, name='attendance_import'),
    path('import/process/', attendance_import_process, name='attendance_import_process'),
    path('import/template/', download_template_absensi, name='attendance_import_template'),
]
