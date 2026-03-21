from django.urls import path
from . import views
from .import_absensi import attendance_import, attendance_import_process, download_template_absensi
from .holiday_manager import (
    holiday_list, holiday_form, holiday_delete,
    holiday_download_template, holiday_import,
    holiday_import_preview, holiday_import_confirm,
)

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
    # Holiday
    path('holiday/', holiday_list, name='holiday_list'),
    path('holiday/tambah/', holiday_form, name='holiday_add'),
    path('holiday/<int:pk>/edit/', holiday_form, name='holiday_edit'),
    path('holiday/<int:pk>/hapus/', holiday_delete, name='holiday_delete'),
    path('holiday/import/', holiday_import, name='holiday_import'),
    path('holiday/import/preview/', holiday_import_preview, name='holiday_import_preview'),
    path('holiday/import/confirm/', holiday_import_confirm, name='holiday_import_confirm'),
    path('holiday/template/', holiday_download_template, name='holiday_download_template'),
    # Import fingerprint
    path('import/', attendance_import, name='attendance_import'),
    path('import/process/', attendance_import_process, name='attendance_import_process'),
    path('import/template/', download_template_absensi, name='attendance_import_template'),
]
