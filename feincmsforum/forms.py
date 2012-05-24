# -*- coding: utf-8 -*-
from datetime import datetime

from django import forms
from django.utils.translation import ugettext as _

from models import Topic, Post, Profile, Report


SORT_USER_BY_CHOICES = (
    ('username', _(u'Username')),
    ('registered', _(u'Registered')),
    ('num_posts', _(u'No. of posts')),
)

SORT_POST_BY_CHOICES = (
    ('0', _(u'Post time')),
    ('1', _(u'Author')),
    ('2', _(u'Subject')),
    ('3', _(u'Forum')),
)

SORT_DIR_CHOICES = (
    ('ASC', _(u'Ascending')),
    ('DESC', _(u'Descending')),
)

SHOW_AS_CHOICES = (
    ('topics', _(u'Topics')),
    ('posts', _(u'Posts')),
)

SEARCH_IN_CHOICES = (
    ('all', _(u'Message text and topic subject')),
    ('message', _(u'Message text only')),
    ('topic', _(u'Topic subject only')),
)

class AddPostForm(forms.ModelForm):
    
    class Meta:
        model = Post
        fields = ['body']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.topic = kwargs.pop('topic', None)
        self.forum = kwargs.pop('forum', None)
        self.ip = kwargs.pop('ip', None)
        super(AddPostForm, self).__init__(*args, **kwargs)

    def clean(self):
        '''
        checking is post subject and body contains not only space characters
        '''
        errmsg = _('Can\'t be empty nor contain only whitespace characters')
        cleaned_data = self.cleaned_data
        body = cleaned_data.get('body')
        subject = cleaned_data.get('name')
        if subject:
            if not subject.strip():
                self._errors['name'] = self.error_class([errmsg])
                del cleaned_data['name']
        if body:
            if not body.strip():
                self._errors['body'] = self.error_class([errmsg])
                del cleaned_data['body']
        return cleaned_data

    def save(self):
        post = Post(topic=self.topic, user=self.user, user_ip=self.ip,
                    body=self.cleaned_data['body'])

        post.save(force_insert=True)
        return post
      
class AddTopicForm(AddPostForm):
    name = forms.CharField(label=_('Subject'), max_length=255)
    
    def save(self):
        self.topic = Topic(forum=self.forum,
                      user=self.user,
                      name=self.cleaned_data['name'])
        self.topic.save()
        return super(AddTopicForm, self).save()

class EditPostForm(forms.ModelForm):
    name = forms.CharField(required=False, label=_('Subject'),
                           widget=forms.TextInput(attrs={'size':'115'}))

    class Meta:
        model = Post
        fields = ['body']

    def __init__(self, *args, **kwargs):
        self.topic = kwargs.pop('topic', None)
        super(EditPostForm, self).__init__(*args, **kwargs)
        self.fields['name'].initial = self.topic

    def save(self, commit=True):
        post = super(EditPostForm, self).save(commit=False)
        post.updated = datetime.now()
        topic_name = self.cleaned_data['name']
        if topic_name:
            post.topic.name = topic_name
        if commit:
            post.topic.save()
            post.save()
        return post


class ForumProfileForm(forms.ModelForm):

    class Meta:
        model = Profile

#    def __init__(self, *args, **kwargs):
#        self.user_view = kwargs.pop('user_view', None)
#        self.user_request = kwargs.pop('user_request', None)
#        self.profile = kwargs['instance']
#        super(EssentialsProfileForm, self).__init__(*args, **kwargs)
#        self.fields['username'].initial = self.user_view.username
#        if not self.user_request.is_superuser:
#            self.fields['username'].widget = forms.HiddenInput()
#        self.fields['email'].initial = self.user_view.email

    def save(self, commit=True):
        if self.cleaned_data:
            if self.user_request.is_superuser:
                self.user_view.username = self.cleaned_data['username']
            self.user_view.email = self.cleaned_data['email']
            self.profile.language = self.cleaned_data['language']
            self.user_view.save()
            if commit:
                self.profile.save()
        return self.profile


class PersonalProfileForm(forms.ModelForm):
    name = forms.CharField(label=_('Real name'), required=False)

    class Meta:
        model = Profile
        fields = ['status', 'location', 'site']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.profile = kwargs['instance']
        super(PersonalProfileForm, self).__init__(*args, **kwargs)
        self.fields['name'].initial = "%s %s" % (self.user.first_name, self.user.last_name)

    def save(self, commit=True):
        self.profile.status = self.cleaned_data['status']
        self.profile.location = self.cleaned_data['location']
        self.profile.site = self.cleaned_data['site']
        if self.cleaned_data['name']:
            cleaned_name = self.cleaned_data['name'].strip()
            if  ' ' in cleaned_name:
                self.user.first_name, self.user.last_name = cleaned_name.split(None, 1)
            else:
                self.user.first_name = cleaned_name
                self.user.last_name = ''
            self.user.save()
            if commit:
                self.profile.save()
        return self.profile

class ReportForm(forms.ModelForm):

    class Meta:
        model = Report
        fields = ['reason', 'post']

    def __init__(self, *args, **kwargs):
        self.reported_by = kwargs.pop('reported_by', None)
        self.post = kwargs.pop('post', None)
        super(ReportForm, self).__init__(*args, **kwargs)
        self.fields['post'].widget = forms.HiddenInput()
        self.fields['post'].initial = self.post
        self.fields['reason'].widget = forms.Textarea(attrs={'rows':'10', 'cols':'75'})

    def save(self, commit=True):
        report = super(ReportForm, self).save(commit=False)
        report.created = datetime.now()
        report.reported_by = self.reported_by
        if commit:
            report.save()
        return report

class PostSearchForm(forms.Form):
    keywords = forms.CharField(required=False, label=_('Keyword search'), 
                               widget=forms.TextInput(attrs={'size':'40', 'maxlength':'100'}))
    author = forms.CharField(required=False, label=_('Author search'),
                             widget=forms.TextInput(attrs={'size':'25', 'maxlength':'25'}))
    forum = forms.CharField(required=False, label=_('Forum'))
    search_in = forms.ChoiceField(choices=SEARCH_IN_CHOICES, label=_('Search in'))
    sort_by = forms.ChoiceField(choices=SORT_POST_BY_CHOICES, label=_('Sort by'))
    sort_dir = forms.ChoiceField(choices=SORT_DIR_CHOICES, initial='DESC', label=_('Sort order'))
    show_as = forms.ChoiceField(choices=SHOW_AS_CHOICES, label=_('Show results as'))


class MailToForm(forms.Form):
    subject = forms.CharField(label=_('Subject'),
                              widget=forms.TextInput(attrs={'size':'75', 'maxlength':'70', 
                                                            'class':'longinput'}))
    body = forms.CharField(required=False, label=_('Message'), 
                               widget=forms.Textarea(attrs={'rows':'10', 'cols':'75'}))
    next_page = forms.CharField(widget=forms.HiddenInput())
