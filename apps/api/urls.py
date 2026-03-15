from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register('employees', views.EmployeeViewSet, basename='api-employee')
router.register('attendance', views.AttendanceViewSet, basename='api-attendance')
router.register('leave', views.LeaveViewSet, basename='api-leave')
router.register('payroll', views.PayrollViewSet, basename='api-payroll')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
