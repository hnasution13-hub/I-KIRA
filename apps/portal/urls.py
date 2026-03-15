from django.urls import path
from . import views

urlpatterns = [
    path('login/',     views.portal_login,     name='portal_login'),
    path('logout/',    views.portal_logout,    name='portal_logout'),
    path('',           views.portal_dashboard, name='portal_dashboard'),
    path('checkin/',   views.portal_checkin,   name='portal_checkin'),
    path('riwayat/',   views.portal_riwayat,   name='portal_riwayat'),
    path('slip-gaji/', views.portal_slip_gaji, name='portal_slip_gaji'),
    path('cuti/',      views.portal_cuti,      name='portal_cuti'),
    path('jadwal/',    views.portal_jadwal,    name='portal_jadwal'),
    path('qa-access/',  views.portal_qa_access,  name='portal_qa_access'),
    path('profile/',     views.portal_profile,     name='portal_profile'),
    path('sync/',        views.portal_sync_checkin, name='portal_sync_checkin'),
    path('offline/',     views.portal_offline,      name='portal_offline'),
]
