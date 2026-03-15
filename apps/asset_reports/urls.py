from django.urls import path
from . import views

app_name = 'asset_reports'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('pic-beban/', views.pic_beban_view, name='pic_beban'),
    path('stock-opname/', views.stock_opname_view, name='stock_opname'),
    path('asset-card/<int:asset_id>/', views.asset_card_view, name='asset_card'),
    path('asset-card/<int:asset_id>/print/', views.asset_card_print, name='asset_card_print'),
    path('depreciation/', views.depreciation_report_view, name='depreciation_report'),
    path('maintenance/', views.maintenance_report_view, name='maintenance_report'),
]