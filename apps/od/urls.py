from django.urls import path
from . import views

app_name = 'od'

urlpatterns = [
    # Dashboard OD
    path('', views.od_dashboard, name='dashboard'),

    # Workload Analysis
    path('workload/', views.workload_list, name='workload_list'),
    path('workload/tambah/', views.workload_create, name='workload_create'),
    path('workload/<int:pk>/edit/', views.workload_edit, name='workload_edit'),
    path('workload/<int:pk>/hapus/', views.workload_delete, name='workload_delete'),

    # FTE Standard
    path('fte-standard/', views.fte_standard_list, name='fte_standard_list'),
    path('fte-standard/tambah/', views.fte_standard_create, name='fte_standard_create'),
    path('fte-standard/<int:pk>/edit/', views.fte_standard_edit, name='fte_standard_edit'),
    path('fte-standard/<int:pk>/hapus/', views.fte_standard_delete, name='fte_standard_delete'),

    # FTE Planning
    path('fte-planning/', views.fte_planning, name='fte_planning'),

    # Performance (dalam konteks OD)
    path('performance/', views.od_performance_dashboard, name='performance'),

    # ── Fase 2: Competency ──────────────────────────────────────────────────
    # Kategori Kompetensi
    path('competency/kategori/', views.competency_category_list, name='competency_category_list'),
    path('competency/kategori/tambah/', views.competency_category_create, name='competency_category_create'),
    path('competency/kategori/<int:pk>/edit/', views.competency_category_edit, name='competency_category_edit'),
    path('competency/kategori/<int:pk>/hapus/', views.competency_category_delete, name='competency_category_delete'),

    # Kompetensi
    path('competency/', views.competency_list, name='competency_list'),
    path('competency/tambah/', views.competency_create, name='competency_create'),
    path('competency/<int:pk>/edit/', views.competency_edit, name='competency_edit'),
    path('competency/<int:pk>/hapus/', views.competency_delete, name='competency_delete'),

    path('competency/jabatan/<int:jabatan_id>/', views.position_competency, name='position_competency'),

    path('competency/matrix/', views.competency_matrix, name='competency_matrix'),
    path('competency/gap-report/', views.competency_gap_report, name='competency_gap_report'),
    path('competency/assess/<int:employee_id>/', views.employee_competency_assess, name='employee_competency_assess'),
]
