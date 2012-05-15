from django.conf.urls.defaults import url, patterns

import views as forum_views
from .feeds import LastPosts, LastTopics, LastPostsOnForum,\
     LastPostsOnCategory, LastPostsOnTopic
     

urlpatterns = patterns('',

    url('^topic/(?P<topic_id>\d+)/stick_unstick/$', 
        forum_views.stick_unstick_topic, name='stick_unstick_topic'),
    url('^topic/(?P<topic_id>\d+)/open_close/$', 
        forum_views.open_close_topic, name='open_close_topic'),
    url('^post/(?P<post_id>\d+)/delete/$', forum_views.delete_post, 
        name='delete_post'),

    url('^post/(?P<post_id>\d+)/$', forum_views.show_post, name='forum_post'),
    
    # Subscription
    url('^subscription/topic/(?P<topic_id>\d+)/$', forum_views.switch_subscription, 
        name='forum_switch_subscription'),
    
    # Feeds
    url(r'^feeds/posts/$', LastPosts(), name='forum_posts_feed'),
    url(r'^feeds/topics/$', LastTopics(), name='forum_topics_feed'),
    url(r'^feeds/topic/(?P<topic_id>\d+)/$', LastPostsOnTopic(), name='forum_topic_feed'),
    url(r'^feeds/forum/(?P<forum_id>\d+)/$', LastPostsOnForum(), name='forum_forum_feed'),
    url(r'^feeds/category/(?P<category_id>\d+)/$', LastPostsOnCategory(), 
        name='forum_category_feed'),
)
