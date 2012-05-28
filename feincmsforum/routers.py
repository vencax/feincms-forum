'''
Created on May 25, 2012

@author: vencax
'''
class PHPBBRouter(object):
    """
    A router for models from phpBB migration package.
    Point all operations on phpbb models to 'phpbb' DB
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'phpbb':
            return 'phpbb'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'phpbb':
            return 'phpbb'
        return None
    
class KunenaRouter(object):
    """
    A router for models from kunena migration package.
    Point all operations on kunena models to 'kunena' DB
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'kunena':
            return 'kunena'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'kunena':
            return 'kunena'
        return None