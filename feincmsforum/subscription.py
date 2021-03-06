from django.conf import settings
from django.utils.html import strip_tags

from util import absolute_url
from django.core.mail import send_mail
from django.template import loader
from django.template.context import Context
from django.contrib.sites.models import Site

template_name = 'feincmsforum/mail/post_notify_mail.html'

def notify_topic_subscribers(post):
    topic = post.topic
    post_body_text = strip_tags(post.body_html)
    t = loader.get_template(template_name)
    unsubscr_url = '%s/%s' % (Site.objects.get_current(), 
                              post.topic.get_absolute_url())
    if post != topic.head:
        for user in topic.subscribers.all():
            if user != post.user:
                subject = u'RE: %s' % topic.name
                to_email = user.email
                
                c = {
                    'username': post.user.username,
                    'message': post_body_text,
                    'post_url': absolute_url(post.get_absolute_url()),
                    'unsubscribe_url': unsubscr_url,
                }
            
                text_content = t.render(Context(c))
                send_mail(subject, text_content, settings.DEFAULT_FROM_EMAIL, [to_email])
