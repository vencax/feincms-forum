# coding=utf-8

from django.core.management.base import BaseCommand
from .export_models.phpbb import PhpBBUser
from django.contrib.auth.models import User
from django.db.transaction import commit_on_success
import datetime
import logging
import re
import leaf

from .export_models.phpbb import PhpBBForum,\
    PhpBBTopic, PhpBBPost, PhpBBGroup
from feincmsforum.models import Category, Forum, Topic, Post, Profile
from .import_util import BaseImporter, prepareImport, unicode_fix, bbcode_formatter
from django.conf import settings



class Command(BaseCommand):
    """
    First import the PhpBB DB backup:
    mysql -u <dbuser> -p <dbname> --default-character-set=utf8 < <backupfile>
    NOTE: do not forget to add router to settings:
    settings.DATABASE_ROUTERS = ['feincmsforum.routers.PHPBBRouter']
    """
    help = u'Imports phpbb sql dump'

    def handle(self, *args, **options):
        logging.basicConfig(level = logging.INFO, **options)
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
        if cat.parent_id == 0:
            return None
        else:
            return PhpBBForum.objects.get(pk=cat.parent_id)

    def _find_root(self, cat):
        curr = self._get_parent(cat)
        while curr.parent_id != 0:
            curr = self._get_parent(curr)
        return curr

    def _get_forumName(self, o):
        return unicode_fix(o.forum_name[:80])


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
        uname = unicode_fix(o.username_clean)
        u = self._get_user(o.user_email, uname)

        if u == None:
            u = User(username=uname,
                     email=o.user_email,
                     password=o.user_password)
            u.save()

        if not Profile.objects.filter(user__exact=u).exists():
            Profile(user=u).save()


class CategoryImporter(BasePhpBBImporter):
    def get_queryset(self):
        return PhpBBForum.objects.filter(parent_id__exact=0)

    @commit_on_success
    def processObject(self, o):
        forumName = self._get_forumName(o)
        if not Category.objects.filter(translations__title__iexact=forumName).exists():
            self._saveCategory(forumName, '')


class ForumImporter(BasePhpBBImporter):
    def get_queryset(self):
        return PhpBBForum.objects.all().exclude(parent_id__exact=0)

    @commit_on_success
    def processObject(self, o):
        forumName = self._get_forumName(o)
        if not Forum.objects.filter(translations__title__iexact=forumName).exists():
            parent = PhpBBForum.objects.get(pk=o.parent_id)
            try:
                category = Category.objects.get(translations__title=self._get_forumName(parent))
            except Category.DoesNotExist:
                root = self._find_root(o)
                try:
                    category = Category.objects.get(translations__title=self._get_forumName(root))
                except Category.DoesNotExist:
                    category = self.blackholeCategory()

            self._saveForum(category, forumName, unicode(o.forum_desc))


class TopicImporter(BasePhpBBImporter):
    def get_queryset(self):
        return PhpBBTopic.objects.all()

    @commit_on_success
    def processObject(self, o):
        if not Topic.objects.filter(name__iexact=o.topic_title).exists():
            try:
                forum = Forum.objects.get(translations__title__iexact=self._get_forumName(o.forum))
            except PhpBBForum.DoesNotExist:
                forum = self.blackholeForum()

            author = self._getAuthor(o)

            createdtime = datetime.datetime.fromtimestamp(o.topic_time)
            Topic(forum=forum, views=o.topic_views, created=createdtime,
                  name=o.topic_title, user=author).save()

class PostImporter(BasePhpBBImporter):
    
    _originalAddress = getattr(settings, 'ORIG_SITE_ADDRESS', '')

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
        if not Post.objects.filter(body__iexact=unicode_fix(o.post_text)).exists():
            author = self._getAuthor(o, o.poster)
            created = datetime.datetime.fromtimestamp(o.post_time)
            try:
                topic = Topic.objects.get(name=unicode_fix(o.topic.topic_title))
            except Topic.DoesNotExist:
                topic = Topic.objects.get(name__icontains=unicode_fix(o.topic.topic_title))

            text = self._process_text(unicode_fix(o.post_text))
            doc = leaf.parse(text)
            text = doc.parse(bbcode_formatter, self._originalAddress)

            Post(topic=topic, body=text, user_ip=o.poster_ip,
                 user=author, created=created).save()

    def _process_text(self, text):
        text = re.sub(self._commentRe, '', text)
        for r, repl in self._regexps.items():
            text = re.sub(r, repl, text)
        return text
