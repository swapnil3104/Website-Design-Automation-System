"""
URL configuration for wireframe-ai project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView, RedirectView
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),

    # API routes — all prefixed with /api/
    path('api/', include('sitemap_app.urls')),

    # Frontend pages served as Django templates from frontend/
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('index.html', RedirectView.as_view(url='/', permanent=True)),
    path('chat', TemplateView.as_view(template_name='chat.html'), name='chat'),
    path('chat.html', RedirectView.as_view(url='/chat', permanent=True)),
    path('wireframe', TemplateView.as_view(template_name='wireframe.html'), name='wireframe'),
    path('wireframe.html', RedirectView.as_view(url='/wireframe', permanent=True)),
]

# Serve static assets directly (CSS/JS) in development
if settings.DEBUG:
    from django.views.static import serve
    FRONTEND_DIR = settings.FRONTEND_DIR
    urlpatterns += [
        re_path(r'^css/(?P<path>.*)$', serve, {'document_root': FRONTEND_DIR / 'css'}),
        re_path(r'^js/(?P<path>.*)$', serve, {'document_root': FRONTEND_DIR / 'js'}),
        re_path(r'^static/css/(?P<path>.*)$', serve, {'document_root': FRONTEND_DIR / 'css'}),
        re_path(r'^static/js/(?P<path>.*)$', serve, {'document_root': FRONTEND_DIR / 'js'}),
        re_path(r'^favicon\.ico$', serve, {'document_root': FRONTEND_DIR, 'path': 'favicon.ico'}),
    ]
