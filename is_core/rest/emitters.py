from __future__ import generators

import datetime, decimal, re, inspect, copy, json


try:
    # yaml isn't standard with python.  It shouldn't be required if it
    # isn't used.
    import yaml
except ImportError:
    yaml = None

# Fallback since `any` isn't in Python <2.5
try:
    any
except NameError:
    def any(iterable):
        for element in iterable:
            if element:
                return True
        return False

from django.db.models.query import QuerySet
from django.db.models import Model, permalink
from django.utils.xmlutils import SimplerXMLGenerator
from django.utils.encoding import smart_unicode, force_text
from django.core.urlresolvers import NoReverseMatch
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponse
from django.core import serializers
from django.utils.translation import ugettext as _
from django.utils import formats, timezone
from django.db.models.fields.files import FileField

from piston.utils import HttpStatusCode, Mimer
from piston.validate_jsonp import is_valid_jsonp_callback_value

from is_core.utils import Enum

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

try:
    import cPickle as pickle
except ImportError:
    import pickle

# Allow people to change the reverser (default `permalink`).
reverser = permalink


class Emitter(object):
    """
    Super emitter. All other emitters should subclass
    this one. It has the `construct` method which
    conveniently returns a serialized `dict`. This is
    usually the only method you want to use in your
    emitter. See below for examples.

    `RESERVED_FIELDS` was introduced when better resource
    method detection came, and we accidentially caught these
    as the methods on the handler. Issue58 says that's no good.
    """
    EMITTERS = { }
    RESERVED_FIELDS = set([ 'read', 'update', 'create',
                            'delete', 'model', 'anonymous',
                            'allowed_methods', 'fields', 'exclude' ])

    SerializationTypes = Enum(('VERBOSE', 'RAW', 'BOTH'))

    def __init__(self, payload, typemapper, handler, request, serialization_format, fields=(), anonymous=True,
                 fun_kwargs={}):
        self.typemapper = typemapper
        self.data = payload
        self.handler = handler
        self.fields = fields
        self.anonymous = anonymous
        self.fun_kwargs = fun_kwargs
        self.request = request
        self.serialization_format = serialization_format

        if isinstance(self.data, Exception):
            raise

    def method_fields(self, handler, fields):
        if not handler:
            return { }

        ret = dict()

        for field in fields - Emitter.RESERVED_FIELDS:
            t = getattr(handler, str(field), None)

            if t and callable(t):
                ret[field] = t

        return ret

    def smart_unicode(self, thing):
        return force_text(thing, strings_only=True)

    def construct(self):
        """
        Recursively serialize a lot of types, and
        in cases where it doesn't recognize the type,
        it will fall back to Django's `smart_unicode`.

        Returns `dict`.
        """
        def _any(thing, fields=None):
            """
            Dispatch, all types are routed through here.
            """
            ret = None

            if isinstance(thing, QuerySet):
                ret = _qs(thing, fields)
            elif isinstance(thing, (tuple, list, set)):
                ret = _list(thing, fields)
            elif isinstance(thing, dict):
                ret = _dict(thing, fields)
            elif isinstance(thing, decimal.Decimal):
                ret = str(thing)
            elif isinstance(thing, Model):
                ret = _model(thing, fields)
            elif isinstance(thing, HttpResponse):
                raise HttpStatusCode(thing)
            elif inspect.isfunction(thing):
                if not inspect.getargspec(thing)[0]:
                    ret = _any(thing())
            elif hasattr(thing, '__emittable__'):
                f = thing.__emittable__
                if inspect.ismethod(f) and len(inspect.getargspec(f)[0]) == 1:
                    ret = _any(f())
            elif repr(thing).startswith("<django.db.models.fields.related.RelatedManager"):
                ret = _any(thing.all())
            else:
                ret = self.smart_unicode(thing)

            return ret

        def _fk(data, field):
            """
            Foreign keys.
            """
            return _any(getattr(data, field.name))

        def _related(data, fields=None):
            """
            Foreign keys.
            """
            return [ _model(m, fields) for m in data.iterator() ]

        def _m2m(data, field, fields=None):
            """
            Many to many (re-route to `_model`.)
            """
            return [ _model(m, fields) for m in getattr(data, field.name).iterator() ]

        def _raw(data, field):
            val = getattr(data, field.attname)
            if isinstance(field, FileField) and val:
                val = val.url
            return val

        def _verbose(data, field):
            humanize_method_name = 'get_%s_humanized' % field.attname
            if hasattr(getattr(data, humanize_method_name, None), '__call__'):
                return getattr(data, humanize_method_name)()
            val = _raw(data, field)
            if isinstance(val, bool):
                val = val and _('Yes') or _('No')
            elif field.choices:
                val = getattr(data, 'get_%s_display' % field.attname)()
            elif isinstance(val, datetime.datetime):
                return formats.localize(timezone.template_localtime(val))
            elif isinstance(val, (datetime.date, datetime.time)):
                return formats.localize(val)
            return val

        def _model(data, fields=None):
            """
            Models. Will respect the `fields` and/or
            `exclude` on the handler (see `typemapper`.)
            """
            ret = { }
            handler = self.in_typemapper(type(data), self.anonymous)
            get_absolute_uri = False

            if handler or fields:

                def v(f):
                    """
                    If field has choices this return display value
                    """
                    if self.serialization_format == self.SerializationTypes.RAW:
                        return _raw(data, f)
                    elif self.serialization_format == self.SerializationTypes.VERBOSE:
                        return _verbose(data, f)
                    else:
                        raw = _raw(data, f)
                        verbose = _verbose(data, f)
                        if raw != verbose:
                            return {'_raw': raw, '_verbose': verbose}
                        return raw

                if not fields and handler:
                    fields = getattr(handler, 'fields')
                    """
                    If user has not read permission only get pid of the object
                    """
                    if not handler.has_read_permission(self.request, data):
                        fields = set(('pk',))

                if not fields:
                    """
                    Fields was not specified, try to find teh correct
                    version in the typemapper we were sent.
                    """
                    mapped = self.in_typemapper(type(data), self.anonymous)
                    get_fields = set(mapped.fields)
                    exclude_fields = set(mapped.exclude).difference(get_fields)

                    if 'absolute_uri' in get_fields:
                        get_absolute_uri = True

                    if not get_fields:
                        get_fields = set([ f.attname.replace("_id", "", 1)
                            for f in data._meta.fields + data._meta.virtual_fields])

                    if hasattr(mapped, 'extra_fields'):
                        get_fields.update(mapped.extra_fields)

                    # sets can be negated.
                    for exclude in exclude_fields:
                        if isinstance(exclude, basestring):
                            get_fields.discard(exclude)

                        elif isinstance(exclude, re._pattern_type):
                            for field in get_fields.copy():
                                if exclude.match(field):
                                    get_fields.discard(field)

                else:
                    get_fields = set(fields)

                met_fields = self.method_fields(handler, get_fields)

                for f in data._meta.local_fields + data._meta.virtual_fields:
                    if hasattr(f, 'serialize') and f.serialize \
                       and not any([ p in met_fields for p in [ f.attname, f.name ]]):
                        if not f.rel:
                            if f.attname in get_fields:
                                ret[f.attname] = _any(v(f))
                                get_fields.remove(f.attname)
                        else:
                            if f.attname[:-3] in get_fields:
                                ret[f.name] = _fk(data, f)
                                get_fields.remove(f.name)

                for mf in data._meta.many_to_many:
                    if mf.serialize and mf.attname not in met_fields:
                        if mf.attname in get_fields:
                            ret[mf.name] = _m2m(data, mf)
                            get_fields.remove(mf.name)

                # try to get the remainder of fields
                for maybe_field in get_fields:


                    if isinstance(maybe_field, (list, tuple)):
                        model, fields = maybe_field
                        inst = getattr(data, model, None)

                        if inst:
                            if hasattr(inst, 'all'):
                                ret[model] = _related(inst, fields)
                            elif callable(inst):
                                if len(inspect.getargspec(inst)[0]) == 1:
                                    ret[model] = _any(inst(), fields)
                            else:
                                ret[model] = _model(inst, fields)

                    elif maybe_field in met_fields:
                        # Overriding normal field which has a "resource method"
                        # so you can alter the contents of certain fields without
                        # using different names.
                        ret[maybe_field] = _any(met_fields[maybe_field](data, **self.fun_kwargs))

                    else:
                        maybe = getattr(data, maybe_field, None)
                        if maybe is not None:
                            if callable(maybe):
                                if len(inspect.getargspec(maybe)[0]) <= 1:
                                    ret[maybe_field] = _any(maybe())
                            else:
                                ret[maybe_field] = _any(maybe)
                        else:
                            handler_f = getattr(handler or self.handler, maybe_field, None)

                            if handler_f:
                                ret[maybe_field] = _any(handler_f(data, **self.fun_kwargs))

            else:
                for f in data._meta.fields:
                    ret[f.attname] = _any(getattr(data, f.attname))

                fields = dir(data.__class__) + ret.keys()
                add_ons = [k for k in dir(data) if k not in fields]

                for k in add_ons:
                    ret[k] = _any(getattr(data, k))

            # resouce uri
            if self.in_typemapper(type(data), self.anonymous):
                handler = self.in_typemapper(type(data), self.anonymous)
                if hasattr(handler, 'resource_uri'):
                    url_id, fields = handler.resource_uri(data)

                    try:
                        ret['resource_uri'] = reverser(lambda: (url_id, fields))()
                    except NoReverseMatch, e:
                        pass

            if hasattr(data, 'get_api_url') and 'resource_uri' not in ret:
                try: ret['resource_uri'] = data.get_api_url()
                except: pass

            # absolute uri
            if hasattr(data, 'get_absolute_url') and get_absolute_uri:
                try: ret['absolute_uri'] = data.get_absolute_url()
                except: pass

            return ret

        def _qs(data, fields=None):
            """
            Querysets.
            """
            return [ _any(v, fields) for v in data ]

        def _list(data, fields=None):
            """
            Lists.
            """
            return [ _any(v, fields) for v in data ]

        def _dict(data, fields=None):
            """
            Dictionaries.
            """
            return dict([ (k, _any(v, fields)) for k, v in data.iteritems() ])

        # Kickstart the seralizin'.

        return _any(self.data, self.fields)

    def in_typemapper(self, model, anonymous):
        for klass, (km, is_anon) in self.typemapper.iteritems():
            if model is km and is_anon is anonymous:
                return klass

    def render(self):
        """
        This super emitter does not implement `render`,
        this is a job for the specific emitter below.
        """
        raise NotImplementedError("Please implement render.")

    def stream_render(self, request, stream=True):
        """
        Tells our patched middleware not to look
        at the contents, and returns a generator
        rather than the buffered string. Should be
        more memory friendly for large datasets.
        """
        yield self.render(request)

    @classmethod
    def get(cls, format):
        """
        Gets an emitter, returns the class and a content-type.
        """
        if cls.EMITTERS.has_key(format):
            return cls.EMITTERS.get(format)

        raise ValueError("No emitters found for type %s" % format)

    @classmethod
    def register(cls, name, klass, content_type='text/plain'):
        """
        Register an emitter.

        Parameters::
         - `name`: The name of the emitter ('json', 'xml', 'yaml', ...)
         - `klass`: The emitter class.
         - `content_type`: The content type to serve response as.
        """
        cls.EMITTERS[name] = (klass, content_type)

    @classmethod
    def unregister(cls, name):
        """
        Remove an emitter from the registry. Useful if you don't
        want to provide output in one of the built-in emitters.
        """
        return cls.EMITTERS.pop(name, None)


class XMLEmitter(Emitter):
    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                xml.startElement("resource", {})
                self._to_xml(xml, item)
                xml.endElement("resource")
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                xml.startElement(key, {})
                self._to_xml(xml, value)
                xml.endElement(key)
        else:
            xml.characters(smart_unicode(data))

    def render(self, request):
        stream = StringIO.StringIO()

        xml = SimplerXMLGenerator(stream, "utf-8")
        xml.startDocument()
        xml.startElement("response", {})

        self._to_xml(xml, self.construct())

        xml.endElement("response")
        xml.endDocument()

        return stream.getvalue()

Emitter.register('xml', XMLEmitter, 'text/xml; charset=utf-8')
Mimer.register(lambda *a: None, ('text/xml',))


class JSONEmitter(Emitter):
    """
    JSON emitter, understands timestamps.
    """
    def render(self, request):
        cb = request.GET.get('callback', None)
        seria = json.dumps(self.construct(), cls=DateTimeAwareJSONEncoder, ensure_ascii=False, indent=4)

        # Callback
        if cb and is_valid_jsonp_callback_value(cb):
            return '%s(%s)' % (cb, seria)

        return seria

Emitter.register('json', JSONEmitter, 'application/json; charset=utf-8')
Mimer.register(json.loads, ('application/json',))


class YAMLEmitter(Emitter):
    """
    YAML emitter, uses `safe_dump` to omit the
    specific types when outputting to non-Python.
    """
    def render(self, request):
        return yaml.safe_dump(self.construct())

if yaml:  # Only register yaml if it was import successfully.
    Emitter.register('yaml', YAMLEmitter, 'application/x-yaml; charset=utf-8')
    Mimer.register(lambda s: dict(yaml.safe_load(s)), ('application/x-yaml',))


class PickleEmitter(Emitter):
    """
    Emitter that returns Python pickled.
    """
    def render(self, request):
        return pickle.dumps(self.construct())

Emitter.register('pickle', PickleEmitter, 'application/python-pickle')

"""
WARNING: Accepting arbitrary pickled data is a huge security concern.
The unpickler has been disabled by default now, and if you want to use
it, please be aware of what implications it will have.

Read more: http://nadiana.com/python-pickle-insecure

Uncomment the line below to enable it. You're doing so at your own risk.
"""
# Mimer.register(pickle.loads, ('application/python-pickle',))


class DjangoEmitter(Emitter):
    """
    Emitter for the Django serialized format.
    """
    def render(self, request, format='xml'):
        if isinstance(self.data, HttpResponse):
            return self.data
        elif isinstance(self.data, (int, str)):
            response = self.data
        else:
            response = serializers.serialize(format, self.data, indent=True)

        return response

Emitter.register('django', DjangoEmitter, 'text/xml; charset=utf-8')
