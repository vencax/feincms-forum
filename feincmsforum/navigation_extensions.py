'''
Created on Jun 5, 2012

@author: vencax
'''

from django.utils.translation import ugettext_lazy as _
from feincms.module.page.extensions.navigation import (NavigationExtension, 
                                                       PagePretender)
from .models import Category

class ForumCategoriesNavigationExtension(NavigationExtension):
    name = _('forum categories')

    def children(self, page, **kwargs):
        for category in Category.objects.all():
            yield PagePretender(
                    title=category.translation.title,
                    url='%scat-%s/' % (page.get_absolute_url(), 
                                       category.translation.slug),
                    tree_id=page.tree_id, # pretty funny tree hack
                    lft=0,
                    rght=0,
                    slug=category.translation.slug
                )