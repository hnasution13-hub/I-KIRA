from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('', views.AuditLogListView.as_view(), name='log_list'),
    path('<int:pk>/', views.AuditLogDetailView.as_view(), name='log_detail'),
    path('statistics/', views.statistics_view, name='statistics'),
]