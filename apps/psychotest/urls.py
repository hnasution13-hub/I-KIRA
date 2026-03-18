from django.urls import path
from . import views
from . import views_kraepelin

urlpatterns = [
    # HR — Soal Bank
    path('soal/',               views.soal_bank_list,   name='soal_bank_list'),
    path('soal/add/',           views.soal_bank_form,   name='soal_bank_add'),
    path('soal/<int:pk>/edit/', views.soal_bank_form,   name='soal_bank_edit'),
    path('soal/<int:pk>/delete/', views.soal_bank_delete, name='soal_bank_delete'),

    # HR — Sesi Psikotes Basic
    path('sessions/',                                   views.session_list,            name='psychotest_session_list'),
    path('sessions/create/<int:candidate_pk>/',         views.session_create,          name='psychotest_session_create'),
    path('sessions/create/employee/<int:employee_pk>/', views.session_create_employee, name='psychotest_create_employee'),
    path('sessions/<int:pk>/',                          views.session_detail,          name='psychotest_session_detail'),

    # Public — tes basic
    path('tes/<uuid:token>/',         views.tes_intro,   name='tes_intro'),
    path('tes/<uuid:token>/mulai/',   views.tes_mulai,   name='tes_mulai'),
    path('tes/<uuid:token>/selesai/', views.tes_selesai, name='tes_selesai'),

    # HR — Kraepelin
    path('kraepelin/',                                     views_kraepelin.kraepelin_session_list, name='kraepelin_list'),
    path('kraepelin/create/candidate/<int:candidate_pk>/', views_kraepelin.kraepelin_create,       name='kraepelin_create_candidate'),
    path('kraepelin/create/employee/<int:employee_pk>/',   views_kraepelin.kraepelin_create,       name='kraepelin_create_employee'),
    path('kraepelin/result/<int:pk>/',                     views_kraepelin.kraepelin_result_hr,    name='kraepelin_result_hr'),

    # Public — Kraepelin tes
    path('kraepelin/<uuid:token>/',         views_kraepelin.kraepelin_intro,        name='kraepelin_intro'),
    path('kraepelin/<uuid:token>/tes/',     views_kraepelin.kraepelin_tes,          name='kraepelin_tes'),
    path('kraepelin/<uuid:token>/submit/',  views_kraepelin.kraepelin_submit_baris, name='kraepelin_submit_baris'),
    path('kraepelin/<uuid:token>/selesai/', views_kraepelin.kraepelin_selesai,      name='kraepelin_selesai'),

    # Pipeline
    path('mcu/<int:candidate_pk>/',                       views.mcu_form,        name='mcu_form'),
    path('interview/<int:candidate_pk>/add/',              views.interview_form,   name='interview_add'),
    path('interview/<int:candidate_pk>/edit/<int:pk>/',    views.interview_form,   name='interview_edit'),
    path('rekomendasi/<int:candidate_pk>/',                views.rekomendasi_form, name='rekomendasi_form'),
    path('onboarding/<int:candidate_pk>/',                 views.onboarding_form,  name='onboarding_form'),
]
