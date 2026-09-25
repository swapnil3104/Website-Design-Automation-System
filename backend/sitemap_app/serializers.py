from rest_framework import serializers
from .models import Sitemap, Page


class PageSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ['page_id', 'name', 'description', 'children']

    def get_children(self, obj):
        children = obj.children.all()
        return PageSerializer(children, many=True).data


class SitemapSerializer(serializers.ModelSerializer):
    pages = serializers.SerializerMethodField()

    class Meta:
        model = Sitemap
        fields = ['id', 'website_type', 'pages', 'created_at']

    def get_pages(self, obj):
        root_pages = obj.pages.filter(parent=None)
        return PageSerializer(root_pages, many=True).data


class PromptSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=1000)


class SitemapUpdateSerializer(serializers.Serializer):
    sitemap_data = serializers.JSONField()
