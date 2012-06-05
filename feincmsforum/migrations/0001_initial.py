# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Category'
        db.create_table('feincmsforum_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ordering', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
        ))
        db.send_create_signal('feincmsforum', ['Category'])

        # Adding M2M table for field groups on 'Category'
        db.create_table('feincmsforum_category_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('category', models.ForeignKey(orm['feincmsforum.category'], null=False)),
            ('group', models.ForeignKey(orm['auth.group'], null=False))
        ))
        db.create_unique('feincmsforum_category_groups', ['category_id', 'group_id'])

        # Adding model 'CategoryTranslation'
        db.create_table('feincmsforum_categorytranslation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='translations', to=orm['feincmsforum.Category'])),
            ('language_code', self.gf('django.db.models.fields.CharField')(default='cs', max_length=10)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
        ))
        db.send_create_signal('feincmsforum', ['CategoryTranslation'])

        # Adding model 'Forum'
        db.create_table('feincmsforum_forum', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='forums', to=orm['feincmsforum.Category'])),
            ('position', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('feincmsforum', ['Forum'])

        # Adding M2M table for field moderators on 'Forum'
        db.create_table('feincmsforum_forum_moderators', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('forum', models.ForeignKey(orm['feincmsforum.forum'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('feincmsforum_forum_moderators', ['forum_id', 'user_id'])

        # Adding model 'ForumTranslation'
        db.create_table('feincmsforum_forumtranslation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='translations', to=orm['feincmsforum.Forum'])),
            ('language_code', self.gf('django.db.models.fields.CharField')(default='cs', max_length=10)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
        ))
        db.send_create_signal('feincmsforum', ['ForumTranslation'])

        # Adding model 'Topic'
        db.create_table('feincmsforum_topic', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('forum', self.gf('django.db.models.fields.related.ForeignKey')(related_name='topics', to=orm['feincmsforum.Forum'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('views', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
            ('sticky', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('feincmsforum', ['Topic'])

        # Adding M2M table for field subscribers on 'Topic'
        db.create_table('feincmsforum_topic_subscribers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('topic', models.ForeignKey(orm['feincmsforum.topic'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('feincmsforum_topic_subscribers', ['topic_id', 'user_id'])

        # Adding model 'Post'
        db.create_table('feincmsforum_post', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('topic', self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts', to=orm['feincmsforum.Topic'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='posts', to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('updated_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('body', self.gf('feincmsforum.fields.BBCodeTextField')()),
            ('user_ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15, null=True, blank=True)),
        ))
        db.send_create_signal('feincmsforum', ['Post'])

        # Adding model 'Profile'
        db.create_table('feincmsforum_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('feincmsforum.fields.AutoOneToOneField')(related_name='forum_profile', unique=True, to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('site', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('jabber', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('icq', self.gf('django.db.models.fields.CharField')(max_length=12, blank=True)),
            ('msn', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('aim', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('yahoo', self.gf('django.db.models.fields.CharField')(max_length=80, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('signature', self.gf('django.db.models.fields.TextField')(default='', max_length=64, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(default='', max_length=5)),
            ('show_signatures', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('post_count', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
        ))
        db.send_create_signal('feincmsforum', ['Profile'])

        # Adding model 'PostTracking'
        db.create_table('feincmsforum_posttracking', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('feincmsforum.fields.AutoOneToOneField')(to=orm['auth.User'], unique=True)),
            ('topics', self.gf('feincmsforum.fields.JSONField')(null=True)),
            ('last_read', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('feincmsforum', ['PostTracking'])

        # Adding model 'Ban'
        db.create_table('feincmsforum_ban', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='ban_users', unique=True, to=orm['auth.User'])),
            ('reason', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('feincmsforum', ['Ban'])

        # Adding model 'Report'
        db.create_table('feincmsforum_report', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reported_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reported_by', to=orm['auth.User'])),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['feincmsforum.Post'])),
            ('zapped', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('zapped_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='zapped_by', null=True, to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('reason', self.gf('django.db.models.fields.TextField')(default='', max_length=1000, blank=True)),
        ))
        db.send_create_signal('feincmsforum', ['Report'])


    def backwards(self, orm):
        # Deleting model 'Category'
        db.delete_table('feincmsforum_category')

        # Removing M2M table for field groups on 'Category'
        db.delete_table('feincmsforum_category_groups')

        # Deleting model 'CategoryTranslation'
        db.delete_table('feincmsforum_categorytranslation')

        # Deleting model 'Forum'
        db.delete_table('feincmsforum_forum')

        # Removing M2M table for field moderators on 'Forum'
        db.delete_table('feincmsforum_forum_moderators')

        # Deleting model 'ForumTranslation'
        db.delete_table('feincmsforum_forumtranslation')

        # Deleting model 'Topic'
        db.delete_table('feincmsforum_topic')

        # Removing M2M table for field subscribers on 'Topic'
        db.delete_table('feincmsforum_topic_subscribers')

        # Deleting model 'Post'
        db.delete_table('feincmsforum_post')

        # Deleting model 'Profile'
        db.delete_table('feincmsforum_profile')

        # Deleting model 'PostTracking'
        db.delete_table('feincmsforum_posttracking')

        # Deleting model 'Ban'
        db.delete_table('feincmsforum_ban')

        # Deleting model 'Report'
        db.delete_table('feincmsforum_report')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'feincmsforum.ban': {
            'Meta': {'object_name': 'Ban'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reason': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'ban_users'", 'unique': 'True', 'to': "orm['auth.User']"})
        },
        'feincmsforum.category': {
            'Meta': {'object_name': 'Category'},
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ordering': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'})
        },
        'feincmsforum.categorytranslation': {
            'Meta': {'ordering': "['title']", 'object_name': 'CategoryTranslation'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'default': "'cs'", 'max_length': '10'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'translations'", 'to': "orm['feincmsforum.Category']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'feincmsforum.forum': {
            'Meta': {'ordering': "['position']", 'object_name': 'Forum'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'forums'", 'to': "orm['feincmsforum.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderators': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'feincmsforum.forumtranslation': {
            'Meta': {'ordering': "['title']", 'object_name': 'ForumTranslation'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'default': "'cs'", 'max_length': '10'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'translations'", 'to': "orm['feincmsforum.Forum']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'feincmsforum.post': {
            'Meta': {'ordering': "['created']", 'object_name': 'Post'},
            'body': ('feincmsforum.fields.BBCodeTextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'topic': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': "orm['feincmsforum.Topic']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'posts'", 'to': "orm['auth.User']"}),
            'user_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'})
        },
        'feincmsforum.posttracking': {
            'Meta': {'object_name': 'PostTracking'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_read': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'topics': ('feincmsforum.fields.JSONField', [], {'null': 'True'}),
            'user': ('feincmsforum.fields.AutoOneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'feincmsforum.profile': {
            'Meta': {'object_name': 'Profile'},
            'aim': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'icq': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jabber': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '5'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'msn': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'}),
            'post_count': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'show_signatures': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '64', 'blank': 'True'}),
            'site': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'user': ('feincmsforum.fields.AutoOneToOneField', [], {'related_name': "'forum_profile'", 'unique': 'True', 'to': "orm['auth.User']"}),
            'yahoo': ('django.db.models.fields.CharField', [], {'max_length': '80', 'blank': 'True'})
        },
        'feincmsforum.report': {
            'Meta': {'object_name': 'Report'},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feincmsforum.Post']"}),
            'reason': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'reported_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reported_by'", 'to': "orm['auth.User']"}),
            'zapped': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'zapped_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'zapped_by'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'feincmsforum.topic': {
            'Meta': {'ordering': "['-updated']", 'object_name': 'Topic'},
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'forum': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'topics'", 'to': "orm['feincmsforum.Forum']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sticky': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subscriptions'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'views': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'})
        }
    }

    complete_apps = ['feincmsforum']