from django.contrib.sitemaps import Sitemap

from models import Forum, Topic

class ForumSitemap(Sitemap):
    """Sitemap for the Forum model."""

    def items(self):
        """Return the Entry objects to appear in the sitemap."""
        return Forum.objects.all()

    def lastmod(self, obj):
        """Return the last modified date for a given Entry object."""
        return obj.updated
      
class TopicSitemap(Sitemap):
    """Sitemap for the Topic model."""

    def items(self):
        """Return the Entry objects to appear in the sitemap."""
        return Topic.objects.all()

    def lastmod(self, obj):
        """Return the last modified date for a given Entry object."""
        return obj.updated
