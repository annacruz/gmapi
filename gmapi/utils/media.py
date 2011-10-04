# -*- coding: utf-8 *-*
from encoding import StrAndUnicode
from itertools import chain
from urlparse import urljoin
from encoding import force_unicode
from safestrings import mark_safe
import settings
import copy


MEDIA_TYPES = ('css','js')


class Media(StrAndUnicode):
    def __init__(self, media=None, **kwargs):
        if media:
            media_attrs = media.__dict__
        else:
            media_attrs = kwargs

        self._css = {}
        self._js = []

        for name in MEDIA_TYPES:
            getattr(self, 'add_' + name)(media_attrs.get(name, None))

        # Any leftover attributes must be invalid.
        # if media_attrs != {}:
        #     raise TypeError("'class Media' has invalid attribute(s): %s" % ','.join(media_attrs.keys()))

    def __unicode__(self):
        return self.render()

    def render(self):
        return mark_safe(u'\n'.join(chain(*[getattr(self, 'render_' + name)() \
        for name in MEDIA_TYPES])))

    def render_js(self):
        return [u'<script type="text/javascript" src="%s"></script>' \
        % self.absolute_path(path) for path in self._js]

    def render_css(self):
        # To keep rendering order consistent, we can't just iterate over
        #items(). We need to sort the keys, and iterate over the sorted list.
        media = self._css.keys()
        media.sort()
        return chain(*[
            [u'<link href="%s" type="text/css" media="%s" rel="stylesheet" />' \
            % (self.absolute_path(path), medium)
                    for path in self._css[medium]]
                for medium in media])

    def absolute_path(self, path, prefix=None):
        if path.startswith(u'http://') or path.startswith(u'https://') \
        or path.startswith(u'/'):
            return path
        if prefix is None:
            if settings.STATIC_URL is None:
                 # backwards compatibility
                prefix = settings.MEDIA_URL
            else:
                prefix = settings.STATIC_URL
        return urljoin(prefix, path)

    def __getitem__(self, name):
        "Returns a Media object that only contains media of the given type"
        if name in MEDIA_TYPES:
            return Media(**{str(name): getattr(self, '_' + name)})
        raise KeyError('Unknown media type "%s"' % name)

    def add_js(self, data):
        if data:
            for path in data:
                if path not in self._js:
                    self._js.append(path)

    def add_css(self, data):
        if data:
            for medium, paths in data.items():
                for path in paths:
                    if not self._css.get(medium) or path \
                    not in self._css[medium]:
                        self._css.setdefault(medium, []).append(path)

    def __add__(self, other):
        combined = Media()
        for name in MEDIA_TYPES:
            getattr(combined, 'add_' + name)(getattr(self, '_' + name, None))
            getattr(combined, 'add_' + name)(getattr(other, '_' + name, None))
        return combined
class MediaDefiningClass(type):
    "Metaclass for classes that can have media definitions"
    def __new__(cls, name, bases, attrs):
        new_class = super(MediaDefiningClass, cls).__new__(cls, name, bases,
                                                           attrs)
        if 'media' not in attrs:
            new_class.media = media_property(new_class)
        return new_class


def media_property(cls):
    def _media(self):
        # Get the media property of the superclass, if it exists
        if hasattr(super(cls, self), 'media'):
            base = super(cls, self).media
        else:
            base = Media()

        # Get the media definition for this class
        definition = getattr(cls, 'Media', None)
        if definition:
            extend = getattr(definition, 'extend', True)
            if extend:
                if extend == True:
                    m = base
                else:
                    m = Media()
                    for medium in extend:
                        m = m + base[medium]
                return m + Media(definition)
            else:
                return Media(definition)
        else:
            return base
    return property(_media)


class Widget(object):
    __metaclass__ = MediaDefiningClass
    is_hidden = False          # Determines whether this corresponds to an <input type="hidden">.
    needs_multipart_form = False # Determines does this widget need multipart-encrypted form
    is_localized = False
    is_required = False

    def __init__(self, attrs=None):
        if attrs is not None:
            self.attrs = attrs.copy()
        else:
            self.attrs = {}

    def __deepcopy__(self, memo):
        obj = copy.copy(self)
        obj.attrs = self.attrs.copy()
        memo[id(self)] = obj
        return obj

    def render(self, name, value, attrs=None):
        """
        Returns this Widget rendered as HTML, as a Unicode string.

        The 'value' given is not guaranteed to be valid input, so subclass
        implementations should program defensively.
        """
        raise NotImplementedError

    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        attrs = dict(self.attrs, **kwargs)
        if extra_attrs:
            attrs.update(extra_attrs)
        return attrs

    def value_from_datadict(self, data, files, name):
        """
        Given a dictionary of data and this widget's name, returns the value
        of this widget. Returns None if it's not provided.
        """
        return data.get(name, None)

    def _has_changed(self, initial, data):
        """
        Return True if data differs from initial.
        """
        # For purposes of seeing whether something has changed, None is
        # the same as an empty string, if the data or inital value we get
        # is None, replace it w/ u''.
        if data is None:
            data_value = u''
        else:
            data_value = data
        if initial is None:
            initial_value = u''
        else:
            initial_value = initial
        if force_unicode(initial_value) != force_unicode(data_value):
            return True
        return False

    def id_for_label(self, id_):
        """
        Returns the HTML ID attribute of this Widget for use by a <label>,
        given the ID of the field. Returns None if no ID is available.

        This hook is necessary because some widgets have multiple HTML
        elements and, thus, multiple IDs. In that case, this method should
        return an ID value that corresponds to the first ID in the widget's
        tags.
        """
        return id_
    id_for_label = classmethod(id_for_label)
