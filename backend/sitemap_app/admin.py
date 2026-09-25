from django.contrib import admin
from .models import Sitemap, Page


@admin.register(Sitemap)
class SitemapAdmin(admin.ModelAdmin):
    list_display = ['website_type', 'prompt', 'created_at']
    list_filter = ['website_type', 'created_at']
    search_fields = ['prompt', 'website_type']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['name', 'sitemap', 'parent', 'order']
    list_filter = ['sitemap__website_type']
    search_fields = ['name', 'description']
