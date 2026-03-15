from django.urls import path
from . import views
from .views_cycle import (
    cycle_list, cycle_form, cycle_delete,
    cycle_assignment_list, cycle_assignment_form,
    cycle_assignment_delete, cycle_preview,
    cycle_generate_roster,
)

urlpatterns = [
    # Master Shift
    path('', views.shift_list, name='shift_list'),
    path('tambah/', views.shift_form, name='shift_add'),
    path('<int:pk>/edit/', views.shift_form, name='shift_edit'),
    path('<int:pk>/hapus/', views.shift_delete, name='shift_delete'),

    # Assignment
    path('assignment/', views.assignment_list, name='assignment_list'),
    path('assignment/tambah/', views.assignment_form, name='assignment_add'),
    path('assignment/<int:pk>/edit/', views.assignment_form, name='assignment_edit'),
    path('assignment/<int:pk>/hapus/', views.assignment_delete, name='assignment_delete'),

    # Roster
    path('roster/', views.roster_view, name='roster_view'),
    path('roster/save-cell/', views.roster_save_cell, name='roster_save_cell'),
    path('roster/bulk-fill/', views.roster_bulk_fill, name='roster_bulk_fill'),

    # Per karyawan
    path('karyawan/<int:employee_id>/', views.employee_shift_view, name='employee_shift_view'),

    # ── Pola Cyclic (Security / Rolling Schedule) ─────────────────────────
    path('cycle/',                               cycle_list,              name='cycle_list'),
    path('cycle/tambah/',                        cycle_form,              name='cycle_add'),
    path('cycle/<int:pk>/edit/',                 cycle_form,              name='cycle_edit'),
    path('cycle/<int:pk>/hapus/',                cycle_delete,            name='cycle_delete'),

    path('cycle/assignment/',                    cycle_assignment_list,   name='cycle_assignment_list'),
    path('cycle/assignment/tambah/',             cycle_assignment_form,   name='cycle_assignment_add'),
    path('cycle/assignment/<int:pk>/edit/',      cycle_assignment_form,   name='cycle_assignment_edit'),
    path('cycle/assignment/<int:pk>/hapus/',     cycle_assignment_delete, name='cycle_assignment_delete'),

    path('cycle/preview/<int:employee_id>/',     cycle_preview,           name='cycle_preview'),
    path('cycle/generate-roster/',               cycle_generate_roster,   name='cycle_generate_roster'),
]
