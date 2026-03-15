from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('',                                views.perf_dashboard,         name='perf_dashboard'),

    # Periode
    path('periode/',                        views.periode_list,           name='periode_list'),
    path('periode/tambah/',                 views.periode_create,         name='periode_create'),
    path('periode/<int:pk>/edit/',          views.periode_edit,           name='periode_edit'),
    path('periode/<int:pk>/hapus/',         views.periode_delete,         name='periode_delete'),

    # KPI Template
    path('template/',                       views.kpi_template_list,      name='kpi_template_list'),
    path('template/tambah/',                views.kpi_template_create,    name='kpi_template_create'),
    path('template/<int:pk>/edit/',         views.kpi_template_edit,      name='kpi_template_edit'),
    path('template/<int:pk>/hapus/',        views.kpi_template_delete,    name='kpi_template_delete'),

    # Penilaian
    path('penilaian/',                      views.penilaian_list,         name='penilaian_list'),
    path('penilaian/buat/',                 views.penilaian_create,       name='penilaian_create'),
    path('penilaian/<int:pk>/',             views.penilaian_detail,       name='penilaian_detail'),
    path('penilaian/<int:pk>/input-kpi/',   views.penilaian_input_kpi,    name='penilaian_input_kpi'),
    path('penilaian/<int:pk>/review/',      views.penilaian_review_atasan,name='penilaian_review_atasan'),
    path('penilaian/<int:pk>/hapus/',       views.penilaian_delete,       name='penilaian_delete'),

    # KPI Item inline
    path('penilaian/<int:penilaian_pk>/kpi/tambah/', views.kpi_item_add,    name='kpi_item_add'),
    path('kpi-item/<int:pk>/hapus/',                 views.kpi_item_delete, name='kpi_item_delete'),

    # Ranking
    path('ranking/',                        views.ranking_view,           name='perf_ranking'),
]
