from django.conf.urls.defaults import url, patterns

import views as forum_views
from feeds import LastPosts, LastTopics, LastPostsOnForum,\
     LastPostsOnCategory, LastPostsOnTopic
from django.contrib.auth.decorators import login_required
     

urlpatterns = patterns('',

    # Forum
    url('^$', forum_views.index, name='index'),
    url('^(?P<forum_id>\d+)/$', forum_views.show_forum, name='forum'),
    url('^moderate/(?P<forum_id>\d+)/$', forum_views.moderate, name='moderate'),
    url('^report/(?P<post_id>\d+)/$', forum_views.report, name='report'),
    url('^mailto/(?P<username>.*)/$', login_required(forum_views.MailToView.as_view()),
        name='mailto'),

    url('^profileedit/$', forum_views.profile, name='forum_profile_edit'),

    # Topic
    url('^topic/(?P<topic_id>\d+)/$', forum_views.show_topic, 
        name='topic'),
    url('^(?P<forum_id>\d+)/add/$', forum_views.create_topic, 
        name='add_topic'),
    url('^topic/move/$', forum_views.move_topic, name='move_topic'),
    url('^topic/(?P<topic_id>\d+)/stick_unstick/(?P<action>[s|u])/$', 
        forum_views.stick_unstick_topic, name='stick_unstick_topic'),
    url('^topic/(?P<topic_id>\d+)/open_close/(?P<action>[c|o])/$', 
        forum_views.open_close_topic, name='open_close_topic'),

    # Post
    url('^(?P<forum_id>\d+)/(?P<topic_id>\d+)/post/add/$', forum_views.add_post,
        name='add_post'),
    url('^post/(?P<post_id>\d+)/$', forum_views.show_post, name='post'),
    url('^post/(?P<post_id>\d+)/edit/$', forum_views.edit_post, 
        name='edit_post'),
    url('^post/(?P<post_id>\d+)/delete/$', forum_views.delete_post, 
        name='delete_post'),

    # Subscription
    url('^subscription/topic/(?P<topic_id>\d+)/delete/$', 
        forum_views.delete_subscription, name='forum_delete_subscription'),
    url('^subscription/topic/(?P<topic_id>\d+)/add/$', 
        forum_views.add_subscription, name='forum_add_subscription'),
    
    # Feeds
    url(r'^feeds/posts/$', LastPosts(), name='forum_posts_feed'),
    url(r'^feeds/topics/$', LastTopics(), name='forum_topics_feed'),
    url(r'^feeds/topic/(?P<topic_id>\d+)/$', LastPostsOnTopic(), name='forum_topic_feed'),
    url(r'^feeds/forum/(?P<forum_id>\d+)/$', LastPostsOnForum(), name='forum_forum_feed'),
    url(r'^feeds/category/(?P<category_id>\d+)/$', LastPostsOnCategory(), 
        name='forum_category_feed'),
)
