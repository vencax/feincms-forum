import math
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.db.models import Q, F
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _

from util import render_to, paged, build_form
from models import Category, Forum, Topic, Post, Profile, PostTracking
from forms import AddPostForm, EditPostForm,\
    MailToForm, ForumProfileForm, ReportForm, AddTopicForm
from vxkforum import settings as forum_settings
from util import smiles, convert_text_to_html
from templatetags.forum_extras import forum_moderated_by

from django.views.generic.base import TemplateView

@render_to('djangobb_forum/index.html')
def index(request, full=True):
    users_cached = cache.get('users_online', {})
    users_online = users_cached and User.objects.filter(id__in = users_cached.keys()) or []
    guests_cached = cache.get('guests_online', {})
    guest_count = len(guests_cached)
    users_count = len(users_online)

    cats = {}
    forums = {}
    user_groups = request.user.groups.all()
    if request.user.is_anonymous():  # in django 1.1 EmptyQuerySet raise exception
        user_groups = []
    _forums = Forum.objects.filter(
            Q(category__groups__in=user_groups) | \
            Q(category__groups__isnull=True)).select_related('last_post__topic',
                                                            'last_post__user',
                                                            'category')
    for forum in _forums:
        cat = cats.setdefault(forum.category.id,
            {'id': forum.category.id, 'cat': forum.category, 'forums': []})
        cat['forums'].append(forum)
        forums[forum.id] = forum

    cmpdef = lambda a, b: cmp(a['cat'].position, b['cat'].position)
    cats = sorted(cats.values(), cmpdef)

    return {
        'cats': cats,
        'posts': Post.objects.count(),
        'topics': Topic.objects.count(),
        'users': User.objects.count(),
        'users_online': users_online,
        'online_count': users_count,
        'guest_count': guest_count,
        'last_user': User.objects.latest('date_joined'),
    }


@transaction.commit_on_success
@render_to('djangobb_forum/moderate.html')
@paged('topics', forum_settings.FORUM_PAGE_SIZE)
def moderate(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    topics = forum.topics.order_by('-sticky', '-updated').select_related()
    if request.user.is_superuser or request.user in forum.moderators.all():
        topic_ids = request.POST.getlist('topic_id')
        if 'move_topics' in request.POST:
            return {
                'categories': Category.objects.all(),
                'topic_ids': topic_ids,
                'exclude_forum': forum,
                'TEMPLATE': 'djangobb_forum/move_topic.html'
            }
        elif 'delete_topics' in request.POST:
            for topic_id in topic_ids:
                topic = get_object_or_404(Topic, pk=topic_id)
                topic.delete()
            return HttpResponseRedirect(reverse('djangobb:index'))
        elif 'open_topics' in request.POST:
            for topic_id in topic_ids:
                open_close_topic(request, topic_id, 'o')
            return HttpResponseRedirect(reverse('djangobb:index'))
        elif 'close_topics' in request.POST:
            for topic_id in topic_ids:
                open_close_topic(request, topic_id, 'c')
            return HttpResponseRedirect(reverse('djangobb:index'))

        return {'forum': forum,
                'topics': topics,
                #'sticky_topics': forum.topics.filter(sticky=True),
                'paged_qs': topics,
                'posts': forum.posts.count(),
                }
    else:
        raise Http404
        
@login_required
@render_to('djangobb_forum/report.html')
def report(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = build_form(ReportForm, request, reported_by=request.user, post=post_id)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return HttpResponseRedirect(post.get_absolute_url())
    return {'form':form}

@login_required
@render_to('djangobb_forum/report.html')
def markread(request):
    PostTracking.objects.filter(user__id=request.user.id).\
        update(last_read=datetime.now(), topics=None)
    return HttpResponseRedirect(reverse('djangobb:index'))
  
  
class MailToView(TemplateView):
    template_name = 'djangobb_forum/mail_to.html'
    
    def get(self, request, *args, **kwargs):
        user = get_object_or_404(User, username=kwargs['username'])
        return self.render_to_response({ 
            'form' : MailToForm(),
            'mailto' : user
        })
      
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, username=kwargs['username'])
        form = MailToForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            body = form.cleaned_data['body'] + '\n %s %s [%s]' % \
                (Site.objects.get_current().domain, 
                 request.user.username,
                 request.user.email)
            user.email_user(subject, body, request.user.email)
            return HttpResponseRedirect(reverse('djangobb:index'))
        return self.render_to_response({'form' : form, 'mailto' : user})


@render_to('djangobb_forum/forum.html')
@paged('topics', forum_settings.FORUM_PAGE_SIZE)
def show_forum(request, forum_id, full=True):
    forum = get_object_or_404(Forum, pk=forum_id)
    if not forum.category.has_access(request.user):
        return HttpResponseForbidden()
    topics = forum.topics.order_by('-sticky', '-updated').select_related()
    moderator = request.user.is_superuser or\
        request.user in forum.moderators.all()
    return {
        'categories': Category.objects.all(),
        'forum': forum,
        'paged_qs': topics,
        'posts': forum.post_count,
        'topics': forum.topic_count,
        'moderator': moderator,
    }

@transaction.commit_on_success
@render_to('djangobb_forum/topic.html')
def show_topic(request, topic_id):
    topic = get_object_or_404(Topic.objects.select_related(), pk=topic_id)
    if not topic.forum.category.has_access(request.user):
        return HttpResponseForbidden()
    Topic.objects.filter(pk=topic.id).update(views=F('views') + 1)

    last_post = topic.last_post

    if request.user.is_authenticated():
        topic.update_read(request.user)
    #@paged can't be used in this view. (ticket #180)
    #TODO: must be refactored (ticket #39)
    from django.core.paginator import Paginator, EmptyPage, InvalidPage
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    paginator = Paginator(topic.posts.all().select_related(), 
                          forum_settings.TOPIC_PAGE_SIZE)
    try:
        page_obj = paginator.page(page)
    except (InvalidPage, EmptyPage):
        raise Http404
    posts = page_obj.object_list
    users = set(post.user.id for post in posts)
    profiles = Profile.objects.filter(user__pk__in=users)
    profiles = dict((profile.user_id, profile) for profile in profiles)

    for post in posts:
        post.user.forum_profile = profiles[post.user.id]

    initial = {}
    form = AddPostForm(topic=topic, initial=initial)

    moderator = request.user.is_superuser or\
        request.user in topic.forum.moderators.all()
    if request.user.is_authenticated() and request.user in topic.subscribers.all():
        subscribed = True
    else:
        subscribed = False

    highlight_word = request.GET.get('hl', '')
    return {
        'categories': Category.objects.all(),
        'topic': topic,
        'last_post': last_post,
        'form': form,
        'moderator': moderator,
        'subscribed': subscribed,
        'posts': posts,
        'highlight_word': highlight_word,
        
        'page': page,
        'page_obj': page_obj,
        'pages': paginator.num_pages,
        'results_per_page': paginator.per_page,
        'is_paginated': page_obj.has_other_pages(),
    }
      
@transaction.commit_on_success
@render_to('djangobb_forum/add_topic.html')
def create_topic(request, forum_id):
    forum = get_object_or_404(Forum, pk=forum_id)
    if not forum.category.has_access(request.user):
        return HttpResponseForbidden()
    if request.method == 'GET':
        form = AddTopicForm()
    else:
        form = AddTopicForm(request.POST)
        if form.is_valid():
            _inject_form(form, ip=request.META.get('REMOTE_ADDR', None),
                         user=request.user, forum=forum)
            form.save()
            return HttpResponseRedirect('../')
    return {'form' : form, 'forum' : forum}
  
def _inject_form(form, **kwargs):
    for k, v in kwargs.items():
        setattr(form, k, v)

@login_required
@transaction.commit_on_success
@render_to('djangobb_forum/add_post.html')
def add_post(request, forum_id, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    if not topic.forum.category.has_access(request.user):
        return HttpResponseForbidden()
    if topic.closed:
        return HttpResponseRedirect(topic.get_absolute_url())
    
    posts = topic.posts.all().select_related()[:5]
    
    if request.method == 'GET':
        form = AddPostForm()
        if 'post_id' in request.GET:
            post_id = request.GET['post_id']
            post = get_object_or_404(Post, pk=post_id)
            form.fields['body'].initial = '[quote]%s:\n%s[/quote]\n%s' %\
                (unicode(post.user), post.body, _('write here'))
    else:
        form = AddPostForm(request.POST)
        if form.is_valid():
            _inject_form(form, ip=request.META.get('REMOTE_ADDR', None),
                         user=request.user, topic=topic)
            post = form.save();
            return HttpResponseRedirect(post.get_absolute_url())

    return {
        'form': form,
        'posts': posts,
        'topic': topic
    }


@transaction.commit_on_success
@render_to('djangobb_forum/profile_edit.html')
def profile(request):
    form = build_form(ForumProfileForm, request, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return HttpResponseRedirect(reverse('djangobb:index'))
    return {'active_menu':'privacy',
      'form': form,
      'TEMPLATE': 'djangobb_forum/profile/profile_privacy.html'
    }
   
def show_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count = post.topic.posts.filter(created__lt=post.created).count() + 1
    page = math.ceil(count / float(forum_settings.TOPIC_PAGE_SIZE))
    url = '%s?page=%d#post-%d' % (reverse('djangobb:topic', args=[post.topic.id]), page, post.id)
    return HttpResponseRedirect(url)


@login_required
@transaction.commit_on_success
@render_to('djangobb_forum/edit_post.html')
def edit_post(request, post_id):
    from templatetags.forum_extras import forum_editable_by

    post = get_object_or_404(Post, pk=post_id)
    
    if forum_settings.POST_MODIF_DEATHLINE and \
      (datetime.now() - post.created).seconds > forum_settings.POST_MODIF_DEATHLINE:
        return HttpResponseRedirect(post.get_absolute_url())
      
    topic = post.topic
    if not forum_editable_by(post, request.user):
        return HttpResponseRedirect(post.get_absolute_url())
    form = build_form(EditPostForm, request, topic=topic, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.updated_by = request.user
        post.save()
        return HttpResponseRedirect(post.get_absolute_url())

    return {
        'form': form,
        'post': post,
    }

@login_required
@transaction.commit_on_success
@render_to('djangobb_forum/move_topic.html')
def move_topic(request):
    if 'topic_id' in request.GET:
        #if move only 1 topic
        topic_ids = [request.GET['topic_id']]
    else:
        topic_ids = request.POST.getlist('topic_id')
    first_topic = topic_ids[0]
    topic = get_object_or_404(Topic, pk=first_topic)
    from_forum = topic.forum
    if 'to_forum' in request.POST:
        to_forum_id = int(request.POST['to_forum'])
        to_forum = get_object_or_404(Forum, pk=to_forum_id)
        for topic_id in topic_ids:
            topic = get_object_or_404(Topic, pk=topic_id)
            if topic.forum != to_forum:
                if forum_moderated_by(topic, request.user):
                    topic.forum = to_forum
                    topic.save()

        #TODO: not DRY
        try:
            last_post = Post.objects.filter(topic__forum__id=from_forum.id).latest()
        except Post.DoesNotExist:
            last_post = None
        from_forum.last_post = last_post
        from_forum.topic_count = from_forum.topics.count()
        from_forum.post_count = from_forum.posts.count()
        from_forum.save()
        return HttpResponseRedirect(to_forum.get_absolute_url())

    return {'categories': Category.objects.all(),
            'topic_ids': topic_ids,
            'exclude_forum': from_forum,
            }


@login_required
@transaction.commit_on_success
def stick_unstick_topic(request, topic_id, action):

    topic = get_object_or_404(Topic, pk=topic_id)
    if forum_moderated_by(topic, request.user):
        if action == 's':
            topic.sticky = True
        elif action == 'u':
            topic.sticky = False
        topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())

@login_required
@transaction.commit_on_success
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    last_post = post.topic.last_post
    topic = post.topic
    forum = post.topic.forum

    if request.user.is_superuser or \
        request.user in post.topic.forum.moderators.all() or \
        (post.user == request.user and post == last_post):
        allowed = True
    else:
        allowed = False

    if not allowed:
        return HttpResponseRedirect(post.get_absolute_url())

    post.delete()

    try:
        Topic.objects.get(pk=topic.id)
    except Topic.DoesNotExist:
        #removed latest post in topic
        return HttpResponseRedirect(forum.get_absolute_url())
    else:
        return HttpResponseRedirect(topic.get_absolute_url())


@login_required
@transaction.commit_on_success
def open_close_topic(request, topic_id, action):

    topic = get_object_or_404(Topic, pk=topic_id)
    if forum_moderated_by(topic, request.user):
        if action == 'c':
            topic.closed = True
        elif action == 'o':
            topic.closed = False
        topic.save()
    return HttpResponseRedirect(topic.get_absolute_url())
  
  
@login_required
@transaction.commit_on_success
def delete_subscription(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    topic.subscribers.remove(request.user)
    if 'from_topic' in request.GET:
        return HttpResponseRedirect(reverse('djangobb:topic', args=[topic.id]))
    else:
        return HttpResponseRedirect(reverse('djangobb:forum_profile', args=[request.user.username]))

@login_required
@transaction.commit_on_success
def add_subscription(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    topic.subscribers.add(request.user)
    return HttpResponseRedirect(reverse('djangobb:topic', args=[topic.id]))


@login_required
@csrf_exempt
@render_to('djangobb_forum/post_preview.html')
def post_preview(request):
    '''Preview for markitup'''
    markup = request.user.forum_profile.markup
    data = request.POST.get('data', '')

    data = convert_text_to_html(data, markup)
    data = smiles(data)
    return {'data': data}
