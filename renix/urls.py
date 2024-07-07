
from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


def custom_404(request, exception):
    return render(request, '404.html', status=404)


handler404 = 'renix.urls.custom_404'


def custom_500(request):
    return render(request, '500.html', status=500)


handler500 = 'renix.urls.custom_500'

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('quiz.urls')),
    path('accounts/', include('allauth.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
