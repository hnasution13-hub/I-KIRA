from django.urls import path
from . import views
from . import views_analytics

urlpatterns = [
    path('', views.landing_view, name='home'),
    path('landing/', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("dashboard/", views_analytics.dashboard, name="dashboard"),
    path("analytics/", views_analytics.analytics_dashboard, name="analytics_dashboard"),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),

    # Job Library (Jabatan)
    path('job-library/', views.job_library_list, name='job_library_list'),
    path('job-library/add/', views.job_library_form, name='job_library_add'),
    path('job-library/<int:pk>/', views.job_library_detail, name='job_library_detail'),
    path('job-library/<int:pk>/edit/', views.job_library_form, name='job_library_edit'),
    path('job-library/<int:pk>/delete/', views.job_library_delete, name='job_library_delete'),

    # Org Chart
    path('org-chart/', views.orgchart_list, name='orgchart_list'),
    path('org-chart/buat/', views.orgchart_create, name='orgchart_create'),
    path('org-chart/<int:pk>/', views.orgchart_detail, name='orgchart_detail'),
    path('org-chart/<int:pk>/aktifkan/', views.orgchart_activate, name='orgchart_activate'),
    path('org-chart/<int:pk>/json/', views.orgchart_json, name='orgchart_json'),

    # Approval Matrix
    path('approval-matrix/', views.approval_matrix_list, name='approval_matrix_list'),
    path('approval-matrix/tambah/', views.approval_matrix_form, name='approval_matrix_add'),
    path('approval-matrix/<int:pk>/edit/', views.approval_matrix_form, name='approval_matrix_edit'),
    path('approval-matrix/<int:pk>/hapus/', views.approval_matrix_delete, name='approval_matrix_delete'),

    # API (AJAX)
    path('api/position/<int:pk>/', views.api_position_detail, name='api_position_detail'),
    path('api/positions/', views.api_positions_list, name='api_positions_list'),
    path('api/approval-chain/', views.api_approval_chain, name='api_approval_chain'),
    path('api/position/<int:pk>/update-parent/', views.api_position_update_parent, name='api_position_update_parent'),

    # Profil Perusahaan
    path('settings/company/', views.company_profile, name='company_profile'),

    # Tenant List (superuser only)
    path('settings/tenants/', views.tenant_list, name='tenant_list'),

    # Tenant Switcher (superuser only)
    path('switch-tenant/', views.switch_tenant, name='switch_tenant'),
]
