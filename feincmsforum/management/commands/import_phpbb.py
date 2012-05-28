from django.core.management.base import BaseCommand
from .export_models.phpbb import PhpBBUser
from django.contrib.auth.models import User
from django.db.transaction import commit_on_success
import datetime
import logging

from .export_models.phpbb import PhpBBForum,\
    PhpBBTopic, PhpBBPost, PhpBBGroup
from feincmsforum.models import Category, Forum, Topic, Post
from .import_util import BaseImporter, prepareImport


class Command(BaseCommand):
    """
    First import the PhpBB DB backup:
    mysql -u <dbuser> -p <dbname> --default-character-set=utf8 < <backupfile>
    NOTE: do not forget to add router to settings:
    settings.DATABASE_ROUTERS = ['feincmsforum.routers.PHPBBRouter']
    """
    help = u'Imports phpbb sql dump'

    def handle(self, *args, **options):
        logging.basicConfig(level = logging.INFO)
        prepareImport()
        UserImporter().doImport()
        CategoryImporter().doImport()
        ForumImporter().doImport()
        TopicImporter().doImport()
        PostImporter().doImport()

# ------------------------ importers ------------------------------------------

def processmoderators():
    gm = PhpBBGroup.objects.filter(group_name__exact='GLOBAL_MODERATORS')
    mods = []

class BasePhpBBImporter(BaseImporter):

    def _getAuthor(self, o, bbUser=None):
        if bbUser == None:
            bbUser = PhpBBUser.objects.get(pk=o.topic_poster)
        return User.objects.get(email=bbUser.user_email)


class UserImporter(BasePhpBBImporter):
    def get_queryset(self):
        return PhpBBUser.objects.all()\
                    .exclude(username__icontains='[bot]')\
                    .exclude(username__icontains='[Bot]')\
                    .exclude(username__icontains='[Google]')\
                    .exclude(username__icontains='[crawler]')\
                    .exclude(username__icontains='[spider]')\
                    .exclude(username__exact='Anonymous')

    @commit_on_success
    def processObject(self, o):
        if not User.objects.filter(email__exact=o.user_email).exists():
            User(username=o.username,
                 email=o.user_email).save()


class CategoryImporter(BasePhpBBImporter):
    def get_queryset(self):
        return PhpBBForum.objects.filter(parent_id__exact=0)

    @commit_on_success
    def processObject(self, o):
        if not Category.objects.filter(name__icontains=o.forum_name).exists():
            Category(name=o.forum_name).save()


class ForumImporter(BasePhpBBImporter):
    def get_queryset(self):
        return PhpBBForum.objects.all().exclude(parent_id__exact=0)

    @commit_on_success
    def processObject(self, o):
        if not Forum.objects.filter(name__icontains=o.forum_name).exists():
            parent = PhpBBForum.objects.get(pk=o.parent_id)
            try:
                category = Category.objects.get(name=parent.forum_name)
            except Category.DoesNotExist:
                category = Category.objects.get(pk=1)

            Forum(category=category, description=o.forum_desc,
                  name=o.forum_name).save()


class TopicImporter(BasePhpBBImporter):
    def get_queryset(self):
        return PhpBBTopic.objects.all()

    @commit_on_success
    def processObject(self, o):
        if not Topic.objects.filter(name__icontains=o.topic_title).exists():
            forum = Forum.objects.get(name=o.forum.forum_name)
            author = self._getAuthor(o)

            createdtime = datetime.datetime.fromtimestamp(o.topic_time)
            Topic(forum=forum, views=o.topic_views, created=createdtime,
                  name=o.topic_title, user=author).save()

class PostImporter(BasePhpBBImporter):
    def get_queryset(self):
        return PhpBBPost.objects.all()

    @commit_on_success
    def processObject(self, o):
        if not Post.objects.filter(body__iexact=o.post_text).exists():
            author = self._getAuthor(o, o.poster)
            created = datetime.datetime.fromtimestamp(o.post_time)
            try:
                topic = Topic.objects.get(name=o.topic.topic_title)
            except Topic.DoesNotExist:
                topic = Topic.objects.get(name__icontains=o.topic.topic_title)
#            text = unicode(leaf.parse(unicode(o.post_text)))

            Post(topic=topic, body=unicode(o.post_text), user_ip=o.poster_ip,
                 user=author, created=created).save()
