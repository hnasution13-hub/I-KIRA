from django.urls import path
from . import views

app_name = 'movements'

urlpatterns = [
    path('', views.MovementListView.as_view(), name='movement_list'),
    path('movement/<int:pk>/', views.MovementDetailView.as_view(), name='movement_detail'),
    path('movement/create/', views.MovementCreateView.as_view(), name='movement_create'),
    path('movement/<int:pk>/update/', views.MovementUpdateView.as_view(), name='movement_update'),
    path('movement/<int:pk>/delete/', views.MovementDeleteView.as_view(), name='movement_delete'),

    path('assignments/', views.AssignmentListView.as_view(), name='assignment_list'),
    path('assignment/<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
]