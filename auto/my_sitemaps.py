from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from attendance.models import Attendance


class AttendanceSitemap(Sitemap):
    """Sitemap для услуг (service_detail)"""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Attendance.objects.all()

    def lastmod(self, obj):
        return obj.updated_at if hasattr(obj, 'updated_at') else None

    def location(self, obj):
        return reverse('service_detail', args=[obj.id])


class StaticViewSitemap(Sitemap):
    """Sitemap для статических страниц"""
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return [
            'services_list',
            'privacy_policy',
        ]

    def location(self, item):
        return reverse(item)