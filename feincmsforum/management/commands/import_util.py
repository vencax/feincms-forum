'''
Created on May 28, 2012

@author: vencax
'''
from feincmsforum.models import Post, Category, Forum, CategoryTranslation,\
    ForumTranslation
import logging
from django.conf import settings
from django.contrib.auth.models import User

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
            return Category.objects.get(translations__title='BlackHole')
        except Category.DoesNotExist:
            cat = Category()
            cat.save()
            cat.translations.add(CategoryTranslation(title='BlackHole'))
            return cat
        
    def blackholeForum(self):
        try:
            return Forum.objects.get(translations__title='BlackHole')
        except Forum.DoesNotExist:
            cat = self.blackholeCategory()
            forum = Forum(category=cat)
            forum.save()
            forum.translations.add(ForumTranslation(title='BlackHole', 
                          description='place for topics without forum'))
            return forum
        
    def _saveForum(self, category, title, desc):
        f = Forum(category=category)
        f.save()
        f.translations.add(ForumTranslation(description=desc, title=title))
        return f

    def _saveCategory(self, title, desc):
        c = Category()
        c.save()
        c.translations.add(CategoryTranslation(title=title, description=desc))
        return c
    
    def _get_user(self, email, name):
        if User.objects.filter(email__iexact=email).exists():
            return User.objects.get(email=email)
        if User.objects.filter(username__iexact=name).exists():
            return User.objects.filter(username__iexact=name)
        return None
                
def unicode_fix(s):
    try:
        return s.decode('utf-8')
    except UnicodeDecodeError:
        return s
    except UnicodeEncodeError:
        return s