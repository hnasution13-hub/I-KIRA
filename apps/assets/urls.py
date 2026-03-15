from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('', views.AssetListView.as_view(), name='asset_list'),
    path('asset/<int:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('asset/create/', views.AssetCreateView.as_view(), name='asset_create'),
    path('asset/<int:pk>/update/', views.AssetUpdateView.as_view(), name='asset_update'),
    path('asset/<int:pk>/delete/', views.AssetDeleteView.as_view(), name='asset_delete'),

    # Import bulk
    path('import/', views.import_asset, name='asset_import'),
    path('import/template/', views.download_template_asset, name='asset_import_template'),

    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('category/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('category/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('category/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('categories/hierarchy/', views.CategoryHierarchyView.as_view(), name='category_hierarchy'),
]