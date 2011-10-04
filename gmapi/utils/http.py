# -*- coding: utf-8 *-*
import urllib
from utils import allow_lazy
from encoding import force_unicode, smart_str


def urlquote(url, safe='/'):
    """
    A version of Python's urllib.quote() function that can operate on unicode
    strings. The url is first UTF-8 encoded before quoting. The returned string
    can safely be used as part of an argument to a subsequent iri_to_uri() call
    without double-quoting occurring.
    """
    return force_unicode(urllib.quote(smart_str(url), smart_str(safe)))

urlquote = allow_lazy(urlquote, unicode)


def urlquote_plus(url, safe=''):
    """
    A version of Python's urllib.quote_plus() function that can operate on
    unicode strings. The url is first UTF-8 encoded before quoting. The
    returned string can safely be used as part of an argument to a subsequent
    iri_to_uri() call without double-quoting occurring.
    """
    return force_unicode(urllib.quote_plus(smart_str(url), smart_str(safe)))
urlquote_plus = allow_lazy(urlquote_plus, unicode)


def urlencode(query, doseq=0, safe=''):
    """Custom urlencode that leaves static map delimiters ("|", ",", ":") alone.

    Based on Django's unicode-safe version of urllib.quote_plus.

    """
    safe = safe + '|,:'
    if hasattr(query, 'items'):
        query = query.items()
    return '&'.join([urlquote_plus(k, safe) + '=' + urlquote_plus(v, safe)
                     for k, s in query
                     for v in ((isinstance(s, basestring) and [s])
                               or (doseq and hasattr(s, '__len__') and s)
                               or [s])])
