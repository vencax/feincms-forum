'''
Created on May 25, 2012

@author: vencax
'''

from django.db import models

class KunenaUser(models.Model):
    class Meta:
        db_table = 'jos_users'
        app_label = 'kunena'

    email = models.EmailField()
    username = models.CharField()
    name = models.CharField()

    def __unicode__(self): return 'KunenaUser %s' % self.username

class KunenaCategory(models.Model):
    class Meta:
        db_table = 'jos_kunena_categories'
        app_label = 'kunena'
        
    name = models.CharField()
    parent = models.IntegerField()
    description = models.CharField()
    
    def __unicode__(self): return 'KunenaCategory %s' % self.name

#class KunenaGroup(models.Model):
#    class Meta:
#        db_table = 'phpbb_groups'
#        app_label = 'kunena'
#
#    group_id = models.IntegerField(primary_key=True)
#    group_name = models.CharField()
#
#    def __unicode__(self): return 'KunenaGroup %s' % self.group_name


class KunenaPost(models.Model):
    class Meta:
        db_table = 'jos_kunena_messages'
        app_label = 'kunena'

    catid = models.IntegerField()
    subject = models.CharField()
    email = models.CharField()
    name = models.CharField()
    thread = models.IntegerField()
    ip = models.IPAddressField()
    time = models.DateTimeField()
    hits = models.IntegerField()
    
    def __unicode__(self): return 'KunenaPost %s' % self.id

class KunenaPostText(models.Model):
    class Meta:
        db_table = 'jos_kunena_messages_text'
        app_label = 'kunena'

    mesid = models.IntegerField(primary_key=True)
    message = models.TextField()