from datetime import datetime

from django.db import models
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save, post_delete

from fields import AutoOneToOneField, JSONField, BBCodeTextField
from feincmsforum.util import convert_text_to_html

if 'south' in settings.INSTALLED_APPS:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^feincmsforum\.fields\.AutoOneToOneField',
                                 '^feincmsforum\.fields\.JSONField',
                                 '^feincmsforum\.fields\.ExtendedImageField',
                                 '^ckeditor\.fields\.RichTextField',])
    

class Category(models.Model):
    name = models.CharField(_('Name'), max_length=80)
    groups = models.ManyToManyField(Group,blank=True, null=True, 
                                    verbose_name=_('Groups'), 
                                    help_text=_('Only users from these groups can see this category'))
    position = models.IntegerField(_('Position'), blank=True, default=0)

    class Meta:
        ordering = ['position']
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __unicode__(self):
        return self.name

    def forum_count(self):
        return self.forums.all().count()

    @property
    def topics(self):
        return Topic.objects.filter(forum__category__id=self.id).select_related()

    @property
    def posts(self):
        return Post.objects.filter(topic__forum__category__id=self.id).select_related()

    def has_access(self, user):
        if self.groups.exists():
            if user.is_authenticated(): 
                    if not self.groups.filter(user__pk=user.id).exists():
                        return False
            else:
                return False
        return True


class Forum(models.Model):
    category = models.ForeignKey(Category, related_name='forums', verbose_name=_('Category'))
    name = models.CharField(_('Name'), max_length=80)
    position = models.IntegerField(_('Position'), blank=True, default=0)
    description = models.TextField(_('Description'), blank=True, default='')
    moderators = models.ManyToManyField(User, blank=True, null=True, verbose_name=_('Moderators'))
    updated = models.DateTimeField(_('Updated'), auto_now=True)

    class Meta:
        ordering = ['position']
        verbose_name = _('Forum')
        verbose_name_plural = _('Forums')

    def __unicode__(self):
        return self.name
      
    def _get_last_post(self):
        def _get_last_post_inner():
            topic_children = self.topics.values_list('id', flat=True)
            return Post.objects.filter(topic__id__in=topic_children).latest()
        return _get_cached_prop_val(self, '_last_post', _get_last_post_inner)
    last_post = property(_get_last_post)
      
    def _get_topic_count(self):
        return _get_cached_prop_val(self, '_topic_count', lambda: self.topics.all().count())
    topic_count = property(_get_topic_count)
    
    def _get_post_count(self):
        def _get_post_count_inner():
            cnt = 0
            for t in self.topics.all():
                cnt += t.post_count
            return cnt
        return _get_cached_prop_val(self, '_post_count', _get_post_count_inner)
    post_count = property(_get_post_count)

    @models.permalink
    def get_absolute_url(self):
        return ('forum_forum', (self.id,))

    @property
    def posts(self):
        return Post.objects.filter(topic__forum__id=self.id).select_related()
      

class Topic(models.Model):
    forum = models.ForeignKey(Forum, related_name='topics', verbose_name=_('Forum'))
    name = models.CharField(_('Subject'), max_length=255)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), null=True)
    user = models.ForeignKey(User, verbose_name=_('User'))
    views = models.IntegerField(_('Views count'), blank=True, default=0)
    sticky = models.BooleanField(_('Sticky'), blank=True, default=False)
    closed = models.BooleanField(_('Closed'), blank=True, default=False)
    subscribers = models.ManyToManyField(User, related_name='subscriptions', 
                                         verbose_name=_('Subscribers'), blank=True)
    class Meta:
        ordering = ['-updated']
        get_latest_by = 'updated'
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')

    def __unicode__(self):
        return self.name
      
    def _get_post_count(self):
        return _get_cached_prop_val(self, '_post_count', lambda: self.posts.all().count())
    post_count = property(_get_post_count)
    
    def _get_last_post(self):
        return _get_cached_prop_val(self, '_last_post', lambda: self.posts.all().latest())
    last_post = property(_get_last_post)

    @property
    def head(self):
        try:
            return self.posts.select_related().order_by('created')[0]
        except IndexError:
            return None

    @property
    def reply_count(self):
        return self.post_count - 1

    @models.permalink
    def get_absolute_url(self):
        return ('forum_topic', (self.id,))

    def update_read(self, user):
        tracking = user.posttracking
        #if last_read > last_read - don't check topics
        if tracking.last_read and (tracking.last_read > self.last_post.created):
            return
        if isinstance(tracking.topics, dict):
            #clear topics if len > 5Kb and set last_read to current time
            if len(tracking.topics) > 5120:
                tracking.topics = None
                tracking.last_read = datetime.now()
                tracking.save()
            #update topics if exist new post or does't exist in dict
            if self.last_post.id > tracking.topics.get(str(self.id), 0):
                tracking.topics[str(self.id)] = self.last_post.id
                tracking.save()
        else:
            #initialize topic tracking dict
            tracking.topics = {self.id: self.last_post.id}
            tracking.save()


class Post(models.Model):
    topic = models.ForeignKey(Topic, related_name='posts', verbose_name=_('Topic'))
    user = models.ForeignKey(User, related_name='posts', verbose_name=_('User'))
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    updated = models.DateTimeField(_('Updated'), blank=True, null=True)
    updated_by = models.ForeignKey(User, verbose_name=_('Updated by'), blank=True, null=True)
    body = BBCodeTextField(verbose_name=_('Message'))
    user_ip = models.IPAddressField(_('User IP'), blank=True, null=True)

    class Meta:
        ordering = ['created']
        get_latest_by = 'created'
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        
    def title(self):
        """ Needed for searching """
        return self.topic

    @models.permalink
    def get_absolute_url(self):
        return ('forum_post', (self.id,))
    
    def _get_body_html(self):
        val = convert_text_to_html(self.body)
        return _get_cached_prop_val(self, '_body_html', val)
    body_html = property(_get_body_html)

    def summary(self):
        LIMIT = 50
        tail = len(self.body_html) > LIMIT and '...' or ''
        return self.body[:LIMIT] + tail

    __unicode__ = summary
    

class Profile(models.Model):
    user = AutoOneToOneField(User, related_name='forum_profile', verbose_name=_('User'))
    status = models.CharField(_('Status'), max_length=30, blank=True)
    site = models.URLField(_('Site'), verify_exists=False, blank=True)
    jabber = models.CharField(_('Jabber'), max_length=80, blank=True)
    icq = models.CharField(_('ICQ'), max_length=12, blank=True)
    msn = models.CharField(_('MSN'), max_length=80, blank=True)
    aim = models.CharField(_('AIM'), max_length=80, blank=True)
    yahoo = models.CharField(_('Yahoo'), max_length=80, blank=True)
    location = models.CharField(_('Location'), max_length=30, blank=True)
    signature = models.TextField(_('Signature'), blank=True, default='', 
                                 max_length=64)
    language = models.CharField(_('Language'), max_length=5, default='', 
                                choices=settings.LANGUAGES)
    show_signatures = models.BooleanField(_('Show signatures'), 
                                          blank=True, default=True)
    post_count = models.IntegerField(_('Post count'), blank=True, default=0)

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    def last_post(self):
        posts = Post.objects.filter(user__id=self.user_id).order_by('-created')
        if posts:
            return posts[0].created
        else:
            return  None
          

class PostTracking(models.Model):
    """
    Model for tracking read/unread posts.
    In topics stored ids of topics and last_posts as dict.
    """

    user = AutoOneToOneField(User)
    topics = JSONField(null=True)
    last_read = models.DateTimeField(null=True)

    class Meta:
        verbose_name = _('Post tracking')
        verbose_name_plural = _('Post tracking')

    def __unicode__(self):
        return self.user.username

BAN_REASON_CHOICES = (
    (1, _('spam')),
    (2, _('rude posts')),
)


class Ban(models.Model):
    user = models.OneToOneField(User, verbose_name=_('Banned user'), 
                                related_name='ban_users')
    reason = models.IntegerField(_('Reason'), 
          choices=BAN_REASON_CHOICES, default=1)

    class Meta:
        verbose_name = _('Ban')
        verbose_name_plural = _('Bans')

    def __unicode__(self):
        return self.user.username
      
      
class Report(models.Model):
    reported_by = models.ForeignKey(User, related_name='reported_by', 
                                    verbose_name=_('Reported by'))
    post = models.ForeignKey(Post, verbose_name=_('Post'))
    zapped = models.BooleanField(_('Zapped'), blank=True, default=False)
    zapped_by = models.ForeignKey(User, related_name='zapped_by', blank=True, 
                                  null=True,  verbose_name=_('Zapped by'))
    created = models.DateTimeField(_('Created'), blank=True)
    reason = models.TextField(_('Reason'), blank=True, default='', 
                              max_length=1000)

    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')

    def __unicode__(self):
        return u'%s %s' % (self.reported_by ,self.zapped)

# ------------------------- signals ----------------------------

from .signals import post_saved, topic_saved, ban_saved, ban_deleted, \
    forum_post_deleted

post_save.connect(post_saved, sender=Post, dispatch_uid='forum_post_save')
post_save.connect(topic_saved, sender=Topic, dispatch_uid='forum_topic_save')
post_save.connect(ban_saved, sender=Ban, dispatch_uid='forum_ban_save')

post_delete.connect(ban_deleted, sender=Ban, dispatch_uid='forum_ban_deleted')
post_delete.connect(forum_post_deleted, sender=Post, dispatch_uid='forum_post_deleted')

# ------------------------- privates ------------------------

def _get_cached_prop_val(obj, prop_name, val):
    """ Support function for getting cached property values from models """
    try:
        return getattr(obj, prop_name)
    except AttributeError:
        if hasattr(val, '__call__'):
            val = val()
        setattr(obj, prop_name, val)
        return getattr(obj, prop_name)
