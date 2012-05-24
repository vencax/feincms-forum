import re
from HTMLParser import HTMLParser
from postmarkup import render_bbcode

from django.http import HttpResponse, Http404
from django.utils.functional import Promise
from django.utils.translation import force_unicode, check_for_language
from django.utils.simplejson import JSONEncoder
from django.template.defaultfilters import urlize as django_urlize
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.contrib.sites.models import Site

from . import settings as forum_settings


#compile smiles regexp
_SMILES = [(re.compile(smile_re), path) for smile_re, path in forum_settings.SMILES]


def absolute_url(path):
    return 'http://%s%s' % (Site.objects.get_current().domain, path)


class FeincmsForumMixin(object):
    """
    Class that decides if to render whole page or appropirate
    feincms application content part.
    """
    def get_context_data(self, **kwargs):
        kwargs.update({'view': self})
        return super(FeincmsForumMixin, self).get_context_data(**kwargs)

    def render_to_response(self, context, **response_kwargs):
        if 'app_config' in getattr(self.request, '_feincms_extra_context', {}):
            return self.get_template_names(), context

        return super(FeincmsForumMixin, self).render_to_response(
            context, **response_kwargs)

class LazyJSONEncoder(JSONEncoder):
    """
    This fing need to save django from crashing.
    """

    def default(self, o):
        if isinstance(o, Promise):
            return force_unicode(o)
        else:
            return super(LazyJSONEncoder, self).default(o)


class JsonResponse(HttpResponse):
    """
    HttpResponse subclass that serialize data into JSON format.
    """
    mimetype = 'application/json; charset=utf8'
    
    def __init__(self, data, mimetype='application/json'):
        json_data = LazyJSONEncoder().encode(data)
        super(JsonResponse, self).__init__(
            content=json_data, mimetype=mimetype)


def build_form(Form, _request, GET=False, *args, **kwargs):
    """
    Shorcut for building the form instance of given form class
    """

    if not GET and 'POST' == _request.method:
        form = Form(_request.POST, _request.FILES, *args, **kwargs)
    elif GET and 'GET' == _request.method:
        form = Form(_request.GET, _request.FILES, *args, **kwargs)
    else:
        form = Form(*args, **kwargs)
    return form


class ExcludeTagsHTMLParser(HTMLParser):
        """
        Class for html parsing with excluding specified tags.
        """

        def __init__(self, func, tags=('a', 'pre', 'span')):
            HTMLParser.__init__(self)
            self.func = func
            self.is_ignored = False
            self.tags = tags
            self.html = []

        def handle_starttag(self, tag, attrs):
            self.html.append('<%s%s>' % (tag, self.__html_attrs(attrs)))
            if tag in self.tags:
                self.is_ignored = True

        def handle_data(self, data):
            if not self.is_ignored:
                data = self.func(data)
            self.html.append(data)

        def handle_startendtag(self, tag, attrs):
            self.html.append('<%s%s/>' % (tag, self.__html_attrs(attrs))) 

        def handle_endtag(self, tag):
            self.is_ignored = False
            self.html.append('</%s>' % (tag))

        def handle_entityref(self, name):
            self.html.append('&%s;' % name)

        def handle_charref(self, name):
            self.html.append('&#%s;' % name)

        def unescape(self, s):
            #we don't need unescape data (without this possible XSS-attack)
            return s

        def __html_attrs(self, attrs):
            _attrs = ''
            if attrs:
                _attrs = ' %s' % (' '.join([('%s="%s"' % (k,v)) for k,v in attrs]))
            return _attrs

        def feed(self, data):
            HTMLParser.feed(self, data)
            self.html = ''.join(self.html)


def urlize(data):
    """
    Urlize plain text links in the HTML contents.
   
    Do not urlize content of A and CODE tags.
    """

    parser = ExcludeTagsHTMLParser(django_urlize)
    parser.feed(data)
    urlized_html = parser.html
    parser.close()
    return urlized_html

def _smile_replacer(data):
    for smile, path in _SMILES:
        data = smile.sub(path, data)
    return data

def smiles(data):
    """
    Replace text smiles.
    """
    if not forum_settings.SMILES_SUPPORT:
        return data
    parser = ExcludeTagsHTMLParser(_smile_replacer)
    parser.feed(data)
    smiled_html = parser.html
    parser.close()
    return smiled_html

def paginate(items, request, per_page, total_count=None):
    try:
        page_number = int(request.GET.get('page', 1))
    except ValueError:
        page_number = 1

    paginator = Paginator(items, per_page)
    pages = paginator.num_pages
    try:
        paged_list_name = paginator.page(page_number).object_list
    except (InvalidPage, EmptyPage):
        raise Http404
    return pages, paginator, paged_list_name 

def set_language(request, language):
    """
    Change the language of session of authenticated user.
    """

    if check_for_language(language):
        request.session['django_language'] = language


def convert_text_to_html(text):
    text = render_bbcode(text, encoding='utf-8')
    text = text.replace('http:///', '/')
    if forum_settings.SMILES_SUPPORT:
            text = smiles(text)
    return urlize(text)
