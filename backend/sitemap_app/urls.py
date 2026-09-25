from django.urls import path
from . import views

urlpatterns = [
    path('init-brief/', views.init_brief, name='init_brief'),
    path('generate-sitemap/', views.generate_sitemap, name='generate_sitemap'),
    path('update-sitemap/', views.update_sitemap, name='update_sitemap'),
    path('export-json/', views.export_json, name='export_json'),
    path('generate-wireframe/', views.generate_wireframe, name='generate_wireframe'),
    path('regenerate-section/', views.regenerate_section, name='regenerate_section'),
    path('config/', views.get_config, name='get_config'),
]
