from django.urls import path
from . import views

urlpatterns = [
    # HR — Soal Bank
    path('soal/',              views.soal_bank_list,   name='soal_bank_list'),
    path('soal/add/',          views.soal_bank_form,   name='soal_bank_add'),
    path('soal/<int:pk>/edit/',views.soal_bank_form,   name='soal_bank_edit'),
    path('soal/<int:pk>/delete/', views.soal_bank_delete, name='soal_bank_delete'),

    # HR — Sesi Psikotes
    path('sessions/',                               views.session_list,   name='psychotest_session_list'),
    path('sessions/create/<int:candidate_pk>/',     views.session_create, name='psychotest_session_create'),
    path('sessions/<int:pk>/',                      views.session_detail, name='psychotest_session_detail'),

    # Public — Kandidat kerjakan tes
    path('tes/<uuid:token>/',        views.tes_intro,   name='tes_intro'),
    path('tes/<uuid:token>/mulai/',  views.tes_mulai,   name='tes_mulai'),
    path('tes/<uuid:token>/selesai/',views.tes_selesai, name='tes_selesai'),

    # Pipeline
    path('mcu/<int:candidate_pk>/',                          views.mcu_form,          name='mcu_form'),
    path('interview/<int:candidate_pk>/add/',                 views.interview_form,     name='interview_add'),
    path('interview/<int:candidate_pk>/edit/<int:pk>/',       views.interview_form,     name='interview_edit'),
    path('rekomendasi/<int:candidate_pk>/',                   views.rekomendasi_form,   name='rekomendasi_form'),
    path('onboarding/<int:candidate_pk>/',                    views.onboarding_form,    name='onboarding_form'),
]
