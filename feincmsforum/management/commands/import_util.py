'''
Created on May 28, 2012

@author: vencax
'''
from feincmsforum.models import Post, Category, Forum
import logging
from django.conf import settings

def prepareImport():
    """
    Turn off auto_fill for created field of Post.
    """
    for f in Post._meta.fields:
        if f.attname == 'created':
            f.auto_now_add = False
    settings.NOTIFY_SUBSRIBERS = False
            
            
class BaseImporter(object):
    def doImport(self):
        objects = self.get_queryset()
        for o in objects:
            try:
                logging.info('Processing %s' % o)
                self.processObject(o)
            except Exception, e:
                logging.exception(e)
                
    def blackholeCategory(self):
        try:
            return Category.objects.get(name='BlackHole')
        except Category.DoesNotExist:
            cat = Category(name='BlackHole')
            cat.save()
            return cat
        
    def blackholeForum(self):
        try:
            return Forum.objects.get(name='BlackHole')
        except Forum.DoesNotExist:
            cat = self.blackholeCategory()
            forum = Forum(category=cat, 
                          description='place for topics without forum',
                          name='BlackHole')
            forum.save()
            return forum
                
def unicode_fix(s):
    try:
        return s.decode('utf-8')
    except UnicodeDecodeError:
        return s
    except UnicodeEncodeError:
        return s