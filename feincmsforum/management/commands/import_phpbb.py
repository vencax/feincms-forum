# coding=utf-8

from django.core.management.base import BaseCommand
from .export_models.phpbb import PhpBBUser
from django.contrib.auth.models import User
from django.db.transaction import commit_on_success
import datetime
import logging

from .export_models.phpbb import PhpBBForum,\
    PhpBBTopic, PhpBBPost, PhpBBGroup
from feincmsforum.models import Category, Forum, Topic, Post, Profile
from .import_util import BaseImporter, prepareImport
import re
import leaf


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
        try:
            return User.objects.get(email=bbUser.user_email)
        except User.DoesNotExist:
            return User.objects.get(username__iexact=bbUser.username_clean)

    def _get_parent(self, cat):
        if cat.parent == 0:
            return None
        else:
            return PhpBBForum.objects.get(pk=cat.parent)

    def _find_root(self, cat):
        curr = self._get_parent(cat)
        while curr.parent != 0:
            curr = self._get_parent(curr)
        return curr


class UserImporter(BasePhpBBImporter):
    def get_queryset(self):
        return PhpBBUser.objects.all()\
                    .exclude(username_clean__icontains='[bot]')\
                    .exclude(username_clean__icontains='[google]')\
                    .exclude(username_clean__icontains='[crawler]')\
                    .exclude(username_clean__icontains='[spider]')\
                    .exclude(username_clean__exact='anonymous')

    @commit_on_success
    def processObject(self, o):
        try:
            u = User.objects.get(email__iexact=o.user_email)
        except User.DoesNotExist:
            try:
                u = User.objects.get(username__iexact=o.username_clean)
            except User.DoesNotExist:
                u = User(username=unicode(o.username_clean),
                         email=o.user_email)
                u.save()
        if not Profile.objects.filter(user__exact=u).exists():
            Profile(user=u).save()


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
                root = self._find_root(o)
                category = Category.objects.get(name=root.forum_name)

            Forum(category=category, description=o.forum_desc,
                  name=o.forum_name).save()


class TopicImporter(BasePhpBBImporter):
    def get_queryset(self):
        return PhpBBTopic.objects.all()

    @commit_on_success
    def processObject(self, o):
        if not Topic.objects.filter(name__icontains=o.topic_title).exists():
            try:
                forum = Forum.objects.get(name__icontains=o.forum.forum_name)
            except Forum.DoesNotExist:
                pass
            author = self._getAuthor(o)

            createdtime = datetime.datetime.fromtimestamp(o.topic_time)
            Topic(forum=forum, views=o.topic_views, created=createdtime,
                  name=o.topic_title, user=author).save()

class PostImporter(BasePhpBBImporter):

    _commentRe = re.compile(r'<!-- [^ ]{1,} -->')
    _smileReg = r'<img src="{SMILIES_PATH}/%s.gif" alt="[^\"]{1,}" title="[^\"]{1,}" />'
    _regexps = {
        _smileReg % 'icon_e_smile' : ':)',
        _smileReg % 'icon_e_biggrin' : ':D',
        _smileReg % 'icon_mrgreen' : ':rolleyes:',
        _smileReg % 'icon_lol' : ':lol:',
        _smileReg % 'icon_e_wink' : ';)',
        _smileReg % 'icon_cry' : ':(',     
#        r'&quot;' : '"'
    }
    
    def doCheck(self):
        for p in Post.objects.all():
            if p.body.find('SMILIES_PATH') != -1:
                p.body = self._process_text(p.body)
                p.save()

    def get_queryset(self):
        return PhpBBPost.objects.all()

    @commit_on_success
    def processObject(self, o):
        if not Post.objects.filter(body__iexact=o.post_text).exists():
            author = self._getAuthor(o, o.poster)
            created = datetime.datetime.fromtimestamp(o.post_time)
            try:
                topic = Topic.objects.get(name=unicode(o.topic.topic_title))
            except Topic.DoesNotExist:
                topic = Topic.objects.get(name__icontains=unicode(o.topic.topic_title))
            
            text = unicode(leaf.parse(self._process_text(unicode(o.post_text))))

            Post(topic=topic, body=text, user_ip=o.poster_ip,
                 user=author, created=created).save()

    def _process_text(self, text):
        text = re.sub(self._commentRe, '', text)
        for r, repl in self._regexps.items():
            text = re.sub(r, repl, text)
        return text