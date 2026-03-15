from django.urls import path
from . import views
from . import views_surat
from . import views_pp

urlpatterns = [
    path('violations/',               views.violation_list,        name='violation_list'),
    path('violations/add/',           views.violation_form,        name='violation_add'),
    path('violations/<int:pk>/',      views.violation_detail,      name='violation_detail'),
    path('violations/<int:pk>/edit/', views.violation_form,        name='violation_edit'),
    path('severance/',                views.severance_list,        name='severance_list'),
    path('severance/calculator/',     views.severance_calculator,  name='severance_calculator'),
    path('severance/<int:pk>/',       views.severance_detail,      name='severance_detail'),
    path('pb/',                       views.pb_list,               name='pb_list'),
    path('pb/create/',                views.pb_create,             name='pb_create'),
    path('pb/<int:pk>/',              views.pb_detail,             name='pb_detail'),
    path('pb/<int:pk>/edit/',         views.pb_edit,               name='pb_edit'),
    path('pb/<int:pk>/print/',        views.pb_print,              name='pb_print'),

    # ── Surat Peringatan ──────────────────────────────────────────────────────
    path('sp/',                  views_surat.sp_list,    name='sp_list'),
    path('sp/create/',           views_surat.sp_create,  name='sp_create'),
    path('sp/<int:pk>/',         views_surat.sp_detail,  name='sp_detail'),
    path('sp/<int:pk>/print/',   views_surat.sp_print,   name='sp_print'),
    path('sp/suggest/',          views_surat.sp_suggest, name='sp_suggest'),

    # ── Surat PHK ─────────────────────────────────────────────────────────────
    path('surat-phk/',               views_surat.surat_phk_list,   name='surat_phk_list'),
    path('surat-phk/create/',        views_surat.surat_phk_create, name='surat_phk_create'),
    path('surat-phk/<int:pk>/',      views_surat.surat_phk_detail, name='surat_phk_detail'),
    path('surat-phk/<int:pk>/print/',views_surat.surat_phk_print,  name='surat_phk_print'),

    # ── Surat Keterangan Kerja ────────────────────────────────────────────────
    path('skk/',               views_surat.skk_list,   name='skk_list'),
    path('skk/create/',        views_surat.skk_create, name='skk_create'),
    path('skk/<int:pk>/',      views_surat.skk_detail, name='skk_detail'),
    path('skk/<int:pk>/print/',views_surat.skk_print,  name='skk_print'),

    # ── Peraturan Perusahaan SP ───────────────────────────────────────────────
    path('sp/peraturan/',                views_pp.pp_sp_list,         name='pp_sp_list'),
    path('sp/peraturan/<int:pk>/aktif/', views_pp.pp_sp_toggle_aktif, name='pp_sp_toggle_aktif'),
    path('sp/peraturan/<int:pk>/hapus/', views_pp.pp_sp_delete,       name='pp_sp_delete'),
    path('sp/peraturan/<int:pk>/unduh/', views_pp.pp_sp_download,     name='pp_sp_download'),
]

