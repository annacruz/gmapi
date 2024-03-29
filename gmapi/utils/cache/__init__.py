"""
Caching framework.

This package defines set of cache backends that all conform to a simple API.
In a nutshell, a cache is a set of values -- which can be any object that
may be pickled -- identified by string keys.  For the complete API, see
the abstract BaseCache class in django.core.cache.backends.base.

Client code should not access a cache backend directly; instead it should
either use the "cache" variable made available here, or it should use the
get_cache() function made available here. get_cache() takes a backend URI
(e.g. "memcached://127.0.0.1:11211/") and returns an instance of a backend
cache class.

See docs/topics/cache.txt for information on the public API.
"""
from gmapi.utils import settings
from gmapi.utils import signals

import importlib


# Name for use in settings file --> name of module in "backends" directory.
# Any backend scheme that is not in this dictionary is treated as a Python
# import path to a custom backend.
BACKENDS = {
    'memcached': 'memcached',
    'locmem': 'locmem',
    'file': 'filebased',
    'db': 'db',
    'dummy': 'dummy',
}

DEFAULT_CACHE_ALIAS = 'default'


class ImproperlyConfigured(Exception):
    "Ops! Some configuration are wrong!!!"
    pass


class InvalidCacheBackendError(ImproperlyConfigured):
    pass


def parse_backend_uri(backend_uri):
    """
    Converts the "backend_uri" into a cache scheme ('db', 'memcached', etc), a
    host and any extra params that are required for the backend. Returns a
    (scheme, host, params) tuple.
    """
    if backend_uri.find(':') == -1:
        raise InvalidCacheBackendError("Backend URI must start with scheme://")
    scheme, rest = backend_uri.split(':', 1)
    if not rest.startswith('//'):
        raise InvalidCacheBackendError("Backend URI must start with scheme://")

    host = rest[2:]
    qpos = rest.find('?')
    if qpos != -1:
        params = dict(parse_qsl(rest[qpos+1:]))
        host = rest[2:qpos]
    else:
        params = {}
    if host.endswith('/'):
        host = host[:-1]

    return scheme, host, params

if not settings.CACHES:
    legacy_backend = getattr(settings, 'CACHE_BACKEND', None)
    if legacy_backend:
        import warnings
        warnings.warn(
            "settings.CACHE_* is deprecated; use settings.CACHES instead.",
            DeprecationWarning
        )
    else:
        # The default cache setting is put here so that we
        # can differentiate between a user who has provided
        # an explicit CACHE_BACKEND of locmem://, and the
        # default value. When the deprecation cycle has completed,
        # the default can be restored to global_settings.py
        settings.CACHE_BACKEND = 'locmem://'

    # Mapping for new-style cache backend api
    backend_classes = {
    }
    engine, host, params = parse_backend_uri(settings.CACHE_BACKEND)
    if engine in backend_classes:
        engine = 'django.core.cache.backends.%s' % backend_classes[engine]
    else:
        engine = '%s.CacheClass' % engine
    defaults = {
        'BACKEND': engine,
        'LOCATION': host,
    }
    defaults.update(params)
    settings.CACHES[DEFAULT_CACHE_ALIAS] = defaults

if DEFAULT_CACHE_ALIAS not in settings.CACHES:
    raise ImproperlyConfigured("You must define a '%s' cache" % DEFAULT_CACHE_ALIAS)

def parse_backend_conf(backend, **kwargs):
    """
    Helper function to parse the backend configuration
    that doesn't use the URI notation.
    """
    # Try to get the CACHES entry for the given backend name first
    conf = settings.CACHES.get(backend, None)
    if conf is not None:
        args = conf.copy()
        args.update(kwargs)
        backend = args.pop('BACKEND')
        location = args.pop('LOCATION', '')
        return backend, location, args
    else:
        try:
            # Trying to import the given backend, in case it's a dotted path
            mod_path, cls_name = backend.rsplit('.', 1)
            mod = importlib.import_module(mod_path)
            backend_cls = getattr(mod, cls_name)
        except (AttributeError, ImportError, ValueError):
            raise InvalidCacheBackendError("Could not find backend '%s'" % backend)
        location = kwargs.pop('LOCATION', '')
        return backend, location, kwargs
    raise InvalidCacheBackendError(
        "Couldn't find a cache backend named '%s'" % backend)

def get_cache(backend, **kwargs):
    """
    Function to load a cache backend dynamically. This is flexible by design
    to allow different use cases:

    To load a backend with the old URI-based notation::

        cache = get_cache('locmem://')

    To load a backend that is pre-defined in the settings::

        cache = get_cache('default')

    To load a backend with its dotted import path,
    including arbitrary options::

        cache = get_cache('django.core.cache.backends.memcached.MemcachedCache', **{
            'LOCATION': '127.0.0.1:11211', 'TIMEOUT': 30,
        })

    """
    try:
        if '://' in backend:
            # for backwards compatibility
            backend, location, params = parse_backend_uri(backend)
            if backend in BACKENDS:
                backend = 'django.core.cache.backends.%s' % BACKENDS[backend]
            params.update(kwargs)
            mod = importlib.import_module(backend)
            backend_cls = mod.CacheClass
        else:
            backend, location, params = parse_backend_conf(backend, **kwargs)
            mod_path, cls_name = backend.rsplit('.', 1)
            mod = importlib.import_module(mod_path)
            backend_cls = getattr(mod, cls_name)
    except (AttributeError, ImportError), e:
        raise InvalidCacheBackendError(
            "Could not find backend '%s': %s" % (backend, e))
    return backend_cls(location, params)

cache = get_cache(DEFAULT_CACHE_ALIAS)

# Some caches -- python-memcached in particular -- need to do a cleanup at the
# end of a request cycle. If the cache provides a close() method, wire it up
# here.
if hasattr(cache, 'close'):
    signals.request_finished.connect(cache.close)
