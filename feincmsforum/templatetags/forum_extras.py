# -*- coding: utf-8

from django import template
from django.core.cache import cache
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_unicode
from django.db import settings
from django.utils.html import escape
from django.contrib.humanize.templatetags.humanize import naturalday

from feincmsforum import settings as forum_settings
from feincmsforum.util import convert_text_to_html
from feincmsforum.models import Topic, Category


register = template.Library()

# TODO:
# * rename all tags with forum_ prefix

@register.simple_tag
def link(obj, anchor=u''):
    """
    Return A tag with link to object.
    """

    url = hasattr(obj, 'get_absolute_url') and obj.get_absolute_url() or None
    anchor = anchor or smart_unicode(obj)
    return mark_safe('<a href="%s">%s</a>' % (url, escape(anchor)))

@register.inclusion_tag('feincmsforum/templatetags/jumpto.html')
def jumpto(topic):
    return {
        'topic' : topic,
        'categories': Category.objects.all(),
    }

@register.tag
def forum_time(parser, token):
    try:
        _, time = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('forum_time requires single argument')
    else:
        return ForumTimeNode(time)


class ForumTimeNode(template.Node):
    def __init__(self, time):
        self.time = template.Variable(time)

    def render(self, context):
        time = self.time.resolve(context)
        formated_time = u'%s %s' % (naturalday(time), time.strftime('%H:%M:%S'))
        formated_time = mark_safe(formated_time)
        return formated_time


# TODO: this old code requires refactoring
@register.inclusion_tag('feincmsforum/pagination.html',takes_context=True)
def pagination(context, adjacent_pages=1):
    """
    Return the list of A tags with links to pages.
    """
    page_range = range(
        max(1, context['page'] - adjacent_pages),
        min(context['pages'], context['page'] + adjacent_pages) + 1)
    previous = None
    next_p = None

    if not 1 == context['page']:
        previous = context['page'] - 1

    if not 1 in page_range:
        page_range.insert(0,1)
        if not 2 in page_range:
            page_range.insert(1,'.')

    if not context['pages'] == context['page']:
        next_p = context['page'] + 1

    if not context['pages'] in page_range:
        if not context['pages'] - 1 in page_range:
            page_range.append('.')
        page_range.append(context['pages'])
    get_params = '&'.join(['%s=%s' % (x[0], x[1]) for x in
        context['request'].GET.iteritems() if (x[0] != 'page' and x[0] != 'per_page')])
    if get_params:
        get_params = '?%s&' % get_params
    else:
        get_params = '?'

    return {
        'get_params': get_params,
        'previous': previous,
        'next': next_p,
        'page': context['page'],
        'pages': context['pages'],
        'page_range': page_range,
        'results_per_page': context['results_per_page'],
        'is_paginated': context['is_paginated'],
        }

@register.filter
def has_unreads(topic, user):
    """
    Check if topic has messages which user didn't read.
    """
    if not user.is_authenticated() or\
        (user.posttracking.last_read is not None and\
         user.posttracking.last_read > topic.last_post.created):
            return False
    else:
        if isinstance(user.posttracking.topics, dict):
            if topic.last_post.id > user.posttracking.topics.get(str(topic.id), 0):
                return True
            else:
                return False
        return True



@register.filter
def forum_moderated_by(topic, user):
    """
    Check if user is moderator of topic's forum.
    """
    return user.is_superuser or user in topic.forum.moderators.all()

@register.inclusion_tag('feincmsforum/tag_newesttopics.html')
def newesttopics(count=5):
    return {'topics': Topic.objects.all().order_by('-updated')[:count]}

@register.filter
def forum_editable_by(post, user):
    """
    Check if the post could be edited by the user.
    """

    if user.is_superuser:
        return True
    if post.user == user:
        return True
    if user in post.topic.forum.moderators.all():
        return True
    return False

@register.filter
def html_from_bbcode(bbcode):
    """    """
    return convert_text_to_html(bbcode, 'bbcode')

@register.filter
def forum_posted_by(post, user):
    """
    Check if the post is writed by the user.
    """

    return post.user == user


@register.filter
def can_post_be_deleted(post, request):
    """
    Check if objects are equal.
    """
    return request.user.is_superuser() or \
        (request.user == post.user and post.topic.last_post)


@register.filter
def forum_authority(user):
    posts = user.forum_profile.post_count
    if posts >= forum_settings.AUTHORITY_STEP_10: 
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote10.gif" alt="" />' % (settings.STATIC_URL))
    elif posts >= forum_settings.AUTHORITY_STEP_9: 
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote9.gif" alt="" />' % (settings.STATIC_URL))
    elif posts >= forum_settings.AUTHORITY_STEP_8: 
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote8.gif" alt="" />' % (settings.STATIC_URL))
    elif posts >= forum_settings.AUTHORITY_STEP_7: 
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote7.gif" alt="" />' % (settings.STATIC_URL))
    elif posts >= forum_settings.AUTHORITY_STEP_6: 
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote6.gif" alt="" />' % (settings.STATIC_URL))
    elif posts >= forum_settings.AUTHORITY_STEP_5: 
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote5.gif" alt="" />' % (settings.STATIC_URL))
    elif posts >= forum_settings.AUTHORITY_STEP_4: 
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote4.gif" alt="" />' % (settings.STATIC_URL))
    elif posts >= forum_settings.AUTHORITY_STEP_3: 
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote3.gif" alt="" />' % (settings.STATIC_URL))
    elif posts >= forum_settings.AUTHORITY_STEP_2: 
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote2.gif" alt="" />' % (settings.STATIC_URL))
    elif posts >= forum_settings.AUTHORITY_STEP_1: 
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote1.gif" alt="" />' % (settings.STATIC_URL))
    else:
        return mark_safe('<img src="%sfeincmsforum/img/authority/vote0.gif" alt="" />' % (settings.STATIC_URL))

    
@register.filter
def online(user):
    return cache.get(str(user.id))
