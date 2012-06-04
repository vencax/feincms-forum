from datetime import datetime
from subscription import notify_topic_subscribers
from .models import Post
from django.conf import settings

def post_saved(instance, **kwargs):
    created = kwargs.get('created')
    post = instance
    topic = post.topic

    if created:
        topic.updated = datetime.now()
        profile = post.user.forum_profile
        profile.post_count = post.user.posts.count()
        profile.save(force_update=True)
        if getattr(settings, 'NOTIFY_SUBSRIBERS', True):
            notify_topic_subscribers(post)
    topic.save(force_update=True)

def topic_saved(instance, **kwargs):
    topic = instance
    forum = topic.forum
    forum.updated = topic.updated
    forum.save(force_update=True)
    
def ban_saved(instance, **kwargs):
    #TODO: send info mail
    pass
    
def ban_deleted(instance, **kwargs):
    #TODO: send info mail
    pass
  
def forum_post_deleted(instance, **kwargs):    
    #if post was last in topic - remove topic
    try:
        Post.objects.filter(topic__id=instance.topic.id).latest()
    except Post.DoesNotExist:
        instance.topic.delete()
   
