from django.db import models


class Sitemap(models.Model):
    """Model to store generated sitemaps"""
    prompt = models.TextField()
    website_type = models.CharField(max_length=200)
    sitemap_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.website_type} - {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-created_at']


class Page(models.Model):
    """Model to represent individual pages in a sitemap"""
    sitemap = models.ForeignKey(Sitemap, on_delete=models.CASCADE, related_name='pages')
    page_id = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    description = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
