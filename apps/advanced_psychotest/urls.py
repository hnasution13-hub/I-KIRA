from django.urls import path
from . import views

urlpatterns = [
    # HR — manajemen
    path('',                                      views.session_list,                name='adv_session_list'),
    path('soal-bank/',                            views.soal_bank,                   name='adv_soal_bank'),
    path('kandidat/<int:candidate_pk>/buat/',     views.session_create,              name='adv_session_create'),
    path('karyawan/<int:employee_pk>/buat/',      views.employee_session_create,     name='adv_employee_session_create'),
    path('sesi/<int:pk>/',                        views.session_detail,              name='adv_session_detail'),
    path('sesi/<int:pk>/cetak/',                  views.export_session_detail_pdf,   name='adv_session_print'),

    # Export
    path('export/excel/',                         views.export_excel,                name='adv_export_excel'),

    # Report karyawan
    path('report/',                               views.psychotest_report_all,       name='adv_report_all'),
    path('report/karyawan/<int:employee_pk>/',    views.employee_psychotest_report,  name='adv_employee_report'),

    # Public — kandidat / karyawan mengerjakan tes
    path('tes/<uuid:token>/',                     views.tes_intro,                   name='adv_tes_intro'),
    path('tes/<uuid:token>/mulai/',               views.tes_mulai,                   name='adv_tes_mulai'),
    path('tes/<uuid:token>/selesai/',             views.tes_selesai,                 name='adv_tes_selesai'),
]
