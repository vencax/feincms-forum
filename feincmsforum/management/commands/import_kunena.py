from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.transaction import commit_on_success
from feincmsforum.models import Category, Forum, Topic, Post
import datetime
import logging

from .export_models.kunena import KunenaCategory, KunenaPost, KunenaUser, KunenaPostText
from .import_util import BaseImporter, prepareImport
from django.conf import settings

class Command(BaseCommand):
    """
    First import the Kunena DB backup:
    mysql -u <dbuser> -p <dbname> --default-character-set=utf8 < <backupfile>
    NOTE: do not forget to add router to settings:
    settings.DATABASE_ROUTERS = ['feincmsforum.routers.KunenaRouter']
    """
    help = u'Imports kunena forum sql dump'

    def handle(self, *args, **options):
        logging.basicConfig(level = logging.INFO)        
        prepareImport()
        UserImporter().doImport()
        CategoryImporter().doImport()
        ForumImporter().doImport()
        PostImporter().doImport()

# ------------------------ importers ------------------------------------------

class UserImporter(BaseImporter):
    def get_queryset(self):
        return KunenaUser.objects.all()\
                    .exclude(username__icontains='[bot]')\
                    .exclude(username__icontains='[Google]')\
                    .exclude(username__icontains='[crawler]')\
                    .exclude(username__icontains='[spider]')\
                    .exclude(username__exact='Anonymous')

    @commit_on_success
    def processObject(self, o):
        if not User.objects.filter(email__exact=o.email).exists():
            nameparts = o.name.split(' ')
            if len(nameparts) == 1:
                first_name, last_name = nameparts[0], ''
            else:
                first_name, last_name = nameparts[0], nameparts[1:]
            User(username=o.username, first_name=first_name,
                 last_name=last_name, email=o.email).save()


class CategoryImporter(BaseImporter):
    def get_queryset(self):
        return KunenaCategory.objects.filter(parent__exact=0)

    @commit_on_success
    def processObject(self, o):
        if not Category.objects.filter(name__icontains=o.name).exists():
            Category(name=o.name).save()


class ForumImporter(BaseImporter):
    def get_queryset(self):
        return KunenaCategory.objects.all().exclude(parent__exact=0)

    @commit_on_success
    def processObject(self, o):
        if not Forum.objects.filter(name__icontains=o.name).exists():
            parent = KunenaCategory.objects.get(pk=o.parent)
            try:
                category = Category.objects.get(name=parent.name)
            except Category.DoesNotExist:
                root = _find_root(o)
                category = Category.objects.get(name=root.name)

            Forum(category=category, description=o.description,
                  name=o.name).save()


class PostImporter(BaseImporter):
    def get_queryset(self):
        return KunenaPost.objects.all()

    @commit_on_success
    def processObject(self, o):
        text = KunenaPostText.objects.get(pk=o.id)
        topic = self._solveTopic(o)
        if not Post.objects.filter(body__iexact=text.message).exists():
            author = _get_user(o.email, o.name)
            created = datetime.datetime.fromtimestamp(o.time)

            Post(topic=topic, body=unicode(text.message), user_ip=o.ip,
                 user=author, created=created).save()

    def _solveTopic(self, o):
        try:
            return Topic.objects.get(name=o.subject)
        except Topic.DoesNotExist:
            kunenacat = KunenaCategory.objects.get(pk=o.catid)
            forum = Forum.objects.get(name__icontains=kunenacat.name)
            author = _get_user(o.email, o.name)

            createdtime = datetime.datetime.fromtimestamp(o.time)
            topic = Topic(forum=forum, views=o.hits, created=createdtime,
                  name=o.subject, user=author)
            topic.save()
            return topic
        
        
def _get_parent(cat):
    if cat.parent == 0:
        return None
    else:
        return KunenaCategory.objects.get(pk=cat.parent)

def _find_root(cat):
    curr = _get_parent(cat)
    while curr.parent != 0:
        curr = _get_parent(curr)
    return curr

def _get_user(email, name):
    if User.objects.filter(email__exact=email).exists():
        return User.objects.get(email=email)
    if User.objects.filter(username__iexact=name).exists():
        return User.objects.filter(username__iexact=name)[0]
    return None