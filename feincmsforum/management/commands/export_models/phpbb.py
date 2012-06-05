'''
Created on May 25, 2012

@author: vencax
'''

from django.db import models
from ..import_util import unicode_fix

class PhpBBUser(models.Model):
    class Meta:
        db_table = 'phpbb_users'
        app_label = 'phpbb'

    user_id = models.IntegerField(primary_key=True)
    user_email = models.EmailField()
    username_clean = models.CharField()
    user_password = models.CharField()

    def __unicode__(self):
        return 'PhpBBUser ' + unicode_fix(self.username_clean)


class PhpBBGroup(models.Model):
    class Meta:
        db_table = 'phpbb_groups'
        app_label = 'phpbb'

    group_id = models.IntegerField(primary_key=True)
    group_name = models.CharField()

    def __unicode__(self):
        return 'PhpBBGroup %s' % unicode_fix(self.group_name)


class PhpBBForum(models.Model):
    class Meta:
        db_table = 'phpbb_forums'
        app_label = 'phpbb'

    forum_id = models.IntegerField(primary_key=True)
    parent_id = models.IntegerField(primary_key=True)
    forum_name = models.CharField()
    forum_desc = models.CharField()
    moderators = models.ManyToManyField(PhpBBUser, through='phpbb_moderator_cache')

    def __unicode__(self):
        return 'PhpBBForum %s' % unicode_fix(self.forum_name)


class PhpBBTopic(models.Model):
    class Meta:
        db_table = 'phpbb_topics'
        app_label = 'phpbb'

    _field_mapping = {
        'title' : 'topic_title',
        'created' : 'topic_time'
    }

    topic_id = models.IntegerField(primary_key=True)
    forum = models.ForeignKey(PhpBBForum)
    topic_title = models.CharField()
    topic_time = models.DateTimeField()
    topic_views = models.IntegerField()
    topic_poster = models.IntegerField()

    def __unicode__(self):
        return 'PhpBBTopic %s' % unicode_fix(self.topic_title)


class PhpBBPost(models.Model):
    class Meta:
        db_table = 'phpbb_posts'
        app_label = 'phpbb'

    post_id = models.IntegerField(primary_key=True)
    topic = models.ForeignKey(PhpBBTopic)
    poster = models.ForeignKey(PhpBBUser)
    poster_ip = models.IPAddressField()
    post_time = models.DateTimeField()
    post_text = models.TextField()

    def __unicode__(self):
        return 'PhpBBPost %s' % self.post_id
