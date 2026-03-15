from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseForbidden


def qa_runner(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden('Akses ditolak.')
    return render(request, 'core/qa_runner.html')


urlpatterns = [
    path('', qa_runner, name='qa_full'),
]
