import math
from datetime import datetime

from django.views.generic.base import TemplateView
from django.conf import settings
from django.views.generic.list import ListView
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

from models import Category, Forum, Topic, Post, Profile, PostTracking
from forms import AddPostForm, EditPostForm,\
    MailToForm, ReportForm, AddTopicForm
from . import settings as forum_settings
from templatetags.forum_extras import forum_moderated_by

from .util import JsonResponse, FeincmsForumMixin, paged, build_form
from django.template.loader import render_to_string

class IndexView(FeincmsForumMixin, TemplateView):
    template_name = 'feincmsforum/index.html'

    def get(self, request, *args, **kwargs):
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

        return self.render_to_response({
            'cats': cats,
            'posts': Post.objects.count(),
            'topics': Topic.objects.count(),
            'users': User.objects.count(),
            'users_online': users_online,
            'online_count': users_count,
            'guest_count': guest_count,
            'last_user': User.objects.latest('date_joined'),
        })


class MailToView(FeincmsForumMixin, TemplateView):
    template_name = 'feincmsforum/mail_to.html'

    def get(self, request, *args, **kwargs):
        user = get_object_or_404(User, username=kwargs['username'])
        next_page = request.GET['nexpage']
        form = MailToForm(initial={'next_page' : next_page})
        return self.render_to_response({
            'form' : form,
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
            return HttpResponseRedirect(form.cleaned_data['next_page'])
        return self.render_to_response({'form' : form, 'mailto' : user})


class ShowForumView(FeincmsForumMixin, ListView):
    template_name = 'feincmsforum/forum.html'
    paginate_by = getattr(settings, 'FORUM_PAGE_SIZE', 15)

    def get_queryset(self):
        self.forum = get_object_or_404(Forum, pk=self.kwargs['forum_id'])
        if not self.forum.category.has_access(self.request.user):
            return HttpResponseForbidden()
        return self.forum.topics.order_by('-sticky', '-updated').select_related()

    def get_context_data(self, **kwargs):
        context = super(ShowForumView, self).get_context_data(**kwargs)
        moderator = self.request.user.is_superuser or\
            self.request.user in self.forum.moderators.all()
        context.update({
            'categories': Category.objects.all(),
            'forum': self.forum,
            'posts': self.forum.post_count,
            'moderator': moderator,
        })
        return context


class ShowTopicView(FeincmsForumMixin, ListView):
    template_name = 'feincmsforum/topic.html'
    paginate_by = getattr(settings, 'FORUM_PAGE_SIZE', 15)

    @transaction.commit_on_success
    def get_queryset(self):
        self.topic = get_object_or_404(Topic.objects.select_related(),
                                       pk=self.kwargs['topic_id'])

        if not self.topic.forum.category.has_access(self.request.user):
            return HttpResponseForbidden()

        Topic.objects.filter(pk=self.topic.id).update(views=F('views') + 1)

        return self.topic.posts.all()

    def get_context_data(self, **kwargs):
        context = super(ShowTopicView, self).get_context_data(**kwargs)

        last_post = self.topic.last_post

        if self.request.user.is_authenticated():
            self.topic.update_read(self.request.user)

        posts = context['page_obj'].object_list
        users = set(post.user.id for post in posts)
        profiles = Profile.objects.filter(user__pk__in=users)
        profiles = dict((profile.user_id, profile) for profile in profiles)

        for post in posts:
            post.user.forum_profile = profiles[post.user.id]

        initial = {}
        form = AddPostForm(topic=self.topic, initial=initial)

        moderator = self.request.user.is_superuser or\
            self.request.user in self.topic.forum.moderators.all()
        if self.request.user.is_authenticated() and \
                self.request.user in self.topic.subscribers.all():
            subscribed = True
        else:
            subscribed = False

        context.update({
            'topic': self.topic,
            'last_post': last_post,
            'form': form,
            'moderator': moderator,
            'subscribed': subscribed,
            'posts': posts
        })
        return context

@transaction.commit_on_success
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
    return 'feincmsforum/add_topic.html', {'form' : form, 'forum' : forum}

def _inject_form(form, **kwargs):
    for k, v in kwargs.items():
        setattr(form, k, v)


@login_required
def report(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = build_form(ReportForm, request, reported_by=request.user, post=post_id)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return HttpResponseRedirect(post.get_absolute_url())
    return 'feincmsforum/report.html', {'form':form}

@login_required
def markread(request):
    PostTracking.objects.filter(user__id=request.user.id).\
        update(last_read=datetime.now(), topics=None)
    return HttpResponseRedirect(reverse('forum_index:index'))

@login_required
@transaction.commit_on_success
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

    return 'feincmsforum/add_post.html', {
        'form': form,
        'posts': posts,
        'topic': topic
    }

#
#@transaction.commit_on_success
#@render_to('feincmsforum/profile_edit.html')
#def profile(request):
#    form = build_form(ForumProfileForm, request, instance=request.user)
#    if request.method == 'POST' and form.is_valid():
#        form.save()
#        return HttpResponseRedirect(reverse('forum_index'))
#    return {'active_menu':'privacy',
#      'form': form,
#      'TEMPLATE': 'feincmsforum/profile/profile_privacy.html'
#    }

def show_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count = post.topic.posts.filter(created__lt=post.created).count() + 1
    page = math.ceil(count / float(getattr(settings, 'FORUM_PAGE_SIZE', 15)))
    url = '%s?page=%d#post-%d' % (post.topic.get_absolute_url(), page, post.id)
    return HttpResponseRedirect(url)


@login_required
@transaction.commit_on_success
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

    return 'feincmsforum/edit_post.html', {
        'form': form,
        'post': post,
    }

#@login_required
#@transaction.commit_on_success
#@render_to('feincmsforum/move_topic.html')
#def move_topic(request, topic_id):
#    if 'topic_id' in request.GET:
#        #if move only 1 topic
#        topic_ids = [request.GET['topic_id']]
#    else:
#        topic_ids = request.POST.getlist('topic_id')
#    first_topic = topic_ids[0]
#    topic = get_object_or_404(Topic, pk=first_topic)
#    from_forum = topic.forum
#    if 'to_forum' in request.POST:
#        to_forum_id = int(request.POST['to_forum'])
#        to_forum = get_object_or_404(Forum, pk=to_forum_id)
#        for topic_id in topic_ids:
#            topic = get_object_or_404(Topic, pk=topic_id)
#            if topic.forum != to_forum:
#                if forum_moderated_by(topic, request.user):
#                    topic.forum = to_forum
#                    topic.save()
#
#        #TODO: not DRY
#        try:
#            last_post = Post.objects.filter(topic__forum__id=from_forum.id).latest()
#        except Post.DoesNotExist:
#            last_post = None
#        from_forum.last_post = last_post
#        from_forum.topic_count = from_forum.topics.count()
#        from_forum.post_count = from_forum.posts.count()
#        from_forum.save()
#        return HttpResponseRedirect(to_forum.get_absolute_url())
#
#    return {'categories': Category.objects.all(),
#            'topic_ids': topic_ids,
#            'exclude_forum': from_forum,
#            }

@login_required
@csrf_exempt
@transaction.commit_on_success
def prepare_move_topic(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    if forum_moderated_by(topic, request.user):
        allforums = Forum.objects.all().exclude(id__in=[topic.forum_id]).\
            values_list('id', 'name')
        data = ['%i#%s' % (fId, name) for fId, name in allforums]
        return JsonResponse({'stat' : 'OK', 'data' : data})
    else:
        return JsonResponse({'stat' : 'FAIL',
                             'msg' : _('you are not moderator of this topic')})

@login_required
@csrf_exempt
@transaction.commit_on_success
def move_topic(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    if forum_moderated_by(topic, request.user):
        forum = get_object_or_404(Forum, pk=request.POST['forum_id'])
        topic.forum = forum
        topic.save()
        return JsonResponse({'stat' : 'OK',
                             'msg' : '%s %s' % (_('Forum moved to'), forum),
                             'redir' : forum.get_absolute_url()})
    else:
        return JsonResponse({'stat' : 'FAIL',
                             'msg' : _('you are not moderator of this topic')})

@login_required
@csrf_exempt
@transaction.commit_on_success
def stick_unstick_topic(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    if forum_moderated_by(topic, request.user):
        topic.sticky = not topic.sticky
        topic.save()
        if topic.sticky:
            return JsonResponse({'stat' : 'OK', 'msg' : _('Unstick topic')})
        else:
            return JsonResponse({'stat' : 'OK', 'msg' : _('Stick topic')})
    else:
        return JsonResponse({'stat' : 'FAIL',
                             'msg' : _('you are not moderator of this topic')})

@login_required
@csrf_exempt
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
        return JsonResponse({'stat' : 'FAIL',
                             'msg' : _('you are not moderator of this topic')})

    post.delete()

    try:
        Topic.objects.get(pk=topic.id)
    except Topic.DoesNotExist:
        #removed latest post in topic
        return JsonResponse({'stat' : 'OK',
                             'redir' : forum.get_absolute_url()})
    else:
        return JsonResponse({'stat' : 'OK', 'msg' : _('post deleted')})


@login_required
@csrf_exempt
@transaction.commit_on_success
def open_close_topic(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    if forum_moderated_by(topic, request.user):
        topic.closed = not topic.closed
        topic.save()
        if topic.closed:
            return JsonResponse({'stat' : 'OK', 'msg' : _('Open topic')})
        else:
            return JsonResponse({'stat' : 'OK', 'msg' : _('Close topic')})
    else:
        return JsonResponse({'stat' : 'FAIL',
                             'msg' : _('you are not moderator of this topic')})


@login_required
@csrf_exempt
@transaction.commit_on_success
def switch_subscription(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    if request.user in topic.subscribers.all():
        topic.subscribers.remove(request.user)
        return JsonResponse({'stat' : 'OK', 'msg' : _('Subscribe')})
    else:
        topic.subscribers.add(request.user)
        return JsonResponse({'stat' : 'OK', 'msg' : _('Unsubscribe')})
