# -*- coding: utf-8 *-*
from safestrings import SafeData, mark_safe
from encoding import force_unicode
from utils import allow_lazy


def escape(html):
    """
    Returns the given HTML with ampersands, quotes and angle brackets encoded.
    """
    return mark_safe(force_unicode(html).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;'))
escape = allow_lazy(escape, unicode)


def conditional_escape(html):
    """
    Similar to escape(), except that it doesn't operate on pre-escaped strings.
    """
    if isinstance(html, SafeData):
        return html
    else:
        return escape(html)


def flatatt(attrs):
    """
    Convert a dictionary of attributes to a single string.
    The returned string will contain a leading space followed by key="value",
    XML-style pairs.  It is assumed that the keys do not need to be XML-escaped.
    If the passed dictionary is empty, then return an empty string.
    """
    return u''.join([u' %s="%s"' % (k, conditional_escape(v)) for k, v in attrs.items()])
