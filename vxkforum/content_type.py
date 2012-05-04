from django.db import models
from django.template.loader import render_to_string
from vxkforum.models import Topic

class NewestForumActivityContent(models.Model):

    class Meta:
        abstract = True # Required by FeinCMS, content types must be abstract

    def render(self, **kwargs):
        return render_to_string('djangobb_forum/newestactivity.html', {
            'content': self, # Not required but a convention followed by
                             # all of FeinCMS' bundled content types
            'topic_list': Topic.objects.all().order_by('-updated')[:5],
        })