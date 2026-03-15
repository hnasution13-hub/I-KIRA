from django.urls import path
from . import views

urlpatterns = [
    # Manpower Request
    path('mprf/', views.mprf_list, name='mprf_list'),
    path('mprf/add/', views.mprf_form, name='mprf_add'),
    path('mprf/<int:pk>/edit/', views.mprf_form, name='mprf_edit'),
    path('mprf/<int:pk>/approve/', views.mprf_approve, name='mprf_approve'),

    # Candidates
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidates/add/', views.candidate_form, name='candidate_add'),
    path('candidates/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('candidates/<int:pk>/edit/', views.candidate_form, name='candidate_edit'),
    path('candidates/<int:pk>/print/', views.candidate_print, name='candidate_print'),
    path('candidates/<int:pk>/update-status/', views.candidate_update_status, name='candidate_update_status'),

    # Offering Letter
    path('offering/', views.offering_list, name='offering_list'),
    path('offering/add/', views.offering_form, name='offering_add'),
    path('offering/<int:pk>/edit/', views.offering_form, name='offering_edit'),
    path('offering/<int:pk>/print/', views.offering_print, name='offering_print'),
    path('offering/<int:pk>/update-status/', views.offering_update_status, name='offering_update_status'),
    path('offering/get-template/', views.offering_get_template, name='offering_get_template'),

    # Offering Template
    path('offering-template/', views.template_list, name='template_list'),
    path('offering-template/add/', views.template_form, name='template_add'),
    path('offering-template/<int:pk>/edit/', views.template_form, name='template_edit'),
    path('offering-template/<int:pk>/delete/', views.template_delete, name='template_delete'),

    # Company Setting
    path('company-setting/', views.company_setting, name='company_setting'),

    # ATS
    path('ats-scan/', views.ats_scan, name='ats_scan'),
    path('ats-scan/analyze/', views.ats_analyze, name='ats_analyze'),
    path('ats-scan/save/', views.ats_save_candidate, name='ats_save_candidate'),
]
