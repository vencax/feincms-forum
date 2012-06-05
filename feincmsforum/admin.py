# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Category, Forum, Topic, Post, Profile, Ban
from feincms.translations import admin_translationinline
from .models import CategoryTranslation, ForumTranslation

CategoryTranslationInline = admin_translationinline(CategoryTranslation, 
    prepopulated_fields={'slug': ('title',)})

class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategoryTranslationInline]
    list_display = ['__unicode__',]
    search_fields = ['translations__title']

ForumTranslationInline = admin_translationinline(ForumTranslation, 
    prepopulated_fields={'slug': ('title',)})

class ForumAdmin(admin.ModelAdmin):
    inlines = [ForumTranslationInline]
    list_display = ['__unicode__',]
    search_fields = ['translations__title']

class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'forum', 'created', 'head', 'post_count']
    search_fields = ['name']
    raw_id_fields = ['user', 'subscribers']

class PostAdmin(admin.ModelAdmin):
    list_display = ['topic', 'user', 'created', 'updated', 'summary']
    search_fields = ['body']
    raw_id_fields = ['topic', 'user', 'updated_by']

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'location', 'language']
    raw_id_fields = ['user']

class BanAdmin(admin.ModelAdmin):
    list_display = ['user', 'reason']
    raw_id_fields = ['user']

admin.site.register(Category, CategoryAdmin)
admin.site.register(Forum, ForumAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Ban, BanAdmin)

#admin.site.disable_action('delete_selected')  #disabled, because delete_selected ignoring delete model method