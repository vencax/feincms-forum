from django.conf.urls.defaults import url, patterns

import views as forum_views
from django.contrib.auth.decorators import login_required
     

urlpatterns = patterns('',

    # Forum
    url('^$', forum_views.index, name='forum_index'),
    url('^(?P<forum_id>\d+)/$', forum_views.show_forum, name='forum_forum'),
    url('^moderate/(?P<forum_id>\d+)/$', forum_views.moderate, name='forum_moderate'),
    url('^report/(?P<post_id>\d+)/$', forum_views.report, name='forum_report'),
    url('^mailto/(?P<username>.*)/$', login_required(forum_views.MailToView.as_view()),
        name='forum_mailto'),

    url('^profileedit/$', forum_views.profile, name='forum_profile_edit'),

    # Topic
    url('^topic/(?P<topic_id>\d+)/$', forum_views.show_topic, 
        name='forum_topic'),
    url('^(?P<forum_id>\d+)/add/$', forum_views.create_topic, 
        name='forum_add_topic'),
    url('^topic/move/(?P<topic_id>\d+)/$', forum_views.move_topic, name='forum_move_topic'),

    # Post
    url('^(?P<forum_id>\d+)/(?P<topic_id>\d+)/post/add/$', forum_views.add_post,
        name='forum_add_post'),
    url('^post/(?P<post_id>\d+)/edit/$', forum_views.edit_post, 
        name='forum_edit_post'),
)
