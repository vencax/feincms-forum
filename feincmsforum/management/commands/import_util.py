'''
Created on May 28, 2012

@author: vencax
'''
from feincmsforum.models import Post
from django.db.models.signals import post_save
import logging

def prepareImport():
    """
    Turn off auto_fill for created field of Post as well as
    post_save signal.
    """
    post_save.disconnect(sender=Post, dispatch_uid='forum_post_save')
    for f in Post._meta.fields:
        if f.attname == 'created':
            f.auto_now_add = False
            
            
class BaseImporter(object):
    def doImport(self):
        objects = self.get_queryset()
        for o in objects:
            try:
                logging.info('Processing %s' % o)
                self.processObject(o)
            except Exception, e:
                logging.exception(e)