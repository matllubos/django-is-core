import re

from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import modelform_factory
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor
from django.db import transaction
from django.db.utils import InterfaceError, DatabaseError

from piston.handler import BaseHandler
from piston.utils import get_handler_of_model

from is_core.utils.models import get_model_field_names
from is_core.rest.paginator import Paginator
from is_core.rest.utils import rc
from is_core.filters import get_model_field_or_method_filter
from is_core.filters.exceptions import FilterException


class HeadersResult(object):

    def __init__(self, result, http_headers={}, status_code=200):
        self.result = result
        self.http_headers = http_headers
        self.status_code = status_code


class RestResponse(HeadersResult):

    def __init__(self, msg, http_headers={}, code=200):
        super(RestResponse, self).__init__(result={'messages': msg}, http_headers=http_headers, status_code=code)


class RestOkResponse(RestResponse):

    def __init__(self, msg, http_headers={}, code=200):
        super(RestOkResponse, self).__init__(msg={'success': msg}, http_headers=http_headers, code=code)


class RestErrorResponse(RestResponse):

    def __init__(self, msg, http_headers={}, code=400):
        super(RestErrorResponse, self).__init__(msg={'error': msg}, http_headers=http_headers, code=code)


class DataInvalidException(Exception):
    def __init__(self, errors):
        self.errors = errors


class RestException(Exception):
    message = None

    def __init__(self, message=None):
        super(RestException, self).__init__()
        self.message = message or self.message

    @property
    def errors(self):
        return {'error': self.message}

class ResourceNotFoundException(RestException):
    message = _('Select a valid choice. That choice is not one of the available choices.')


class NotAllowedException(RestException):
    message = _('Create or update this resource is not allowed.')


class DataProcessor(object):
    def __init__(self, request, model, form_fields, inst):
        self.model = model
        self.request = request
        self.form_fields = form_fields
        self.inst = inst

    def _process_field(self, data, key, data_item):
        pass

    def clear_data(self, data):
        return data

    def process_data(self, data):
        data = self.clear_data(data)

        self.errors = {}
        for key, data_item in data.items():
            self._process_field(data, key, data_item)

        if self.errors:
            raise DataInvalidException(self.errors)
        return data


class DataPreprocessor(DataProcessor):

    def _process_list_field(self, handler, data, key, data_items, rel_model):
        """
        Create or update ManyToMany field
        """
        i = 1
        errors = []

        data[key] = []
        for data_item in data_items:
            if isinstance(data_item, dict):
                try:
                    data[key].append(handler._create_or_update(self.request, data_item).pk)
                except (DataInvalidException, ResourceNotFoundException) as ex:
                    er = ex.errors
                    er.update({'_index': i})
                    errors.append(er)
            else:
                data[key].append(data_item)

        if errors:
            self.errors[key] = errors

    def _process_dict_field(self, handler, data, key, data_item, rel_model):
        """
        Create or update ForeignKey field
        """
        try:
            data[key] = handler._create_or_update(self.request, data_item).pk
        except (DataInvalidException, ResourceNotFoundException) as ex:
            self.errors[key] = ex.errors

    def _process_field(self, data, key, data_item):
        if isinstance(data_item, (list, tuple, dict)) and key in self.form_fields.keys() and\
            hasattr(self.form_fields.get(key), 'queryset'):
            rel_model = self.form_fields.get(key).queryset.model
            handler_class = get_handler_of_model(rel_model)
            if handler_class:
                handler = handler_class()

                if isinstance(data_item, (list, tuple)):
                    self._process_list_field(handler, data, key, data_item, rel_model)
                else:
                    self._process_dict_field(handler, data, key, data_item, rel_model)

    def clear_data(self, data):
        return dict([(re.sub('_id$', '', key), val) for key, val in data.items()])


class DataPostprocessor(DataProcessor):

    def _process_list_field(self, handler, data, key, data_item, related_obj):
        """
        Create or update reverse ForeignKey field
        """
        i = 1
        errors = []
        existing_related = []
        for rel_obj_data in data_item:

            if not isinstance(rel_obj_data, dict):
                rel_obj_data = {'id': rel_obj_data}

            rel_obj_data[related_obj.field.name] = self.inst.pk
            try:
                existing_related.append(handler._create_or_update(self.request, rel_obj_data).pk)
            except (DataInvalidException, ResourceNotFoundException) as ex:
                er = ex.errors
                er.update({'_index': i})
                errors.append(er)
            i += 1

        # TODO: Delete other related objects. This will be more complicated.
        for reverse_related_obj in handler.model.objects.filter(**{related_obj.field.name: self.inst})\
                                    .exclude(pk__in=existing_related):
            if handler.has_delete_permission(self.request, reverse_related_obj.pk):
                handler._delete(self.request, reverse_related_obj)

        if errors:
            self.errors[key] = errors

    def _process_field(self, data, key, data_item):
        if key not in self.form_fields.keys() and hasattr(self.model, key) and \
            isinstance(getattr(self.model, key), ForeignRelatedObjectsDescriptor):
            related_obj = getattr(self.model, key).related

            handler_class = get_handler_of_model(related_obj.model)
            if handler_class:
                handler = handler_class()
                self._process_list_field(handler, data, key, data_item, related_obj)


class RestHandler(BaseHandler):

    register = False
    extra_fields = ()
    login_required = True

    @classmethod
    def has_read_permission(cls, request, pk=None):
        return 'GET' in cls.allowed_methods

    @classmethod
    def has_create_permission(cls, request, pk=None):
        return 'POST' in cls.allowed_methods

    @classmethod
    def has_update_permission(cls, request, pk=None):
        return 'PUT' in cls.allowed_methods

    @classmethod
    def has_delete_permission(cls, request, pk=None):
        return 'DELETE' in cls.allowed_methods

    @classmethod
    def get_permission_validators(cls):
        all_permissions_validators = {
                                        'GET': cls.has_read_permission,
                                        'PUT': cls.has_update_permission,
                                        'POST': cls.has_create_permission,
                                        'DELETE': cls.has_delete_permission,
                                    }

        permissions_validators = {}
        for allowed_method in cls.allowed_methods:
            permissions_validators[allowed_method] = all_permissions_validators[allowed_method]
        return permissions_validators

    @classmethod
    def get_allowed_methods(cls, user, obj_pk):
        allowed_methods = []
        for method, validator in cls.get_permission_validators().items():
            if validator(user, obj_pk):
                allowed_methods.append(method)
        return allowed_methods


class RestCoreHandler(RestHandler):

    @classmethod
    def has_read_permission(cls, request, pk=None):
        return super(RestCoreHandler, cls).has_read_permission(request, pk) \
                and cls.core.has_rest_read_permission(request, pk)

    @classmethod
    def has_create_permission(cls, request, pk=None):
        return super(RestCoreHandler, cls).has_create_permission(request) \
                and cls.core.has_rest_create_permission(request, pk)

    @classmethod
    def has_update_permission(cls, request, pk=None):
        return super(RestCoreHandler, cls).has_update_permission(request, pk) \
                and cls.core.has_rest_update_permission(request, pk)

    @classmethod
    def has_delete_permission(cls, request, pk=None):
        return super(RestCoreHandler, cls).has_delete_permission(request, pk) \
                and cls.core.has_rest_delete_permission(request, pk)


class RestModelHandler(RestCoreHandler):

    register = True

    @classmethod
    def _obj_name(cls, obj, request):
        return unicode(obj)

    @classmethod
    def _web_links(cls, obj, request):
        web_links = {}
        for pattern in cls.core.ui_patterns.values():
            url = pattern.get_url_string(obj)
            if url:
                web_links[pattern.name] = url
        return web_links

    @classmethod
    def _rest_links(cls, obj, request):
        rest_links = {}
        for pattern in cls.core.resource_patterns.values():
            url = pattern.get_url_string(obj)
            if url:
                rest_links[pattern.name] = {'url': url, 'methods': pattern.get_allowed_methods(request, obj)}
        return rest_links

    @classmethod
    def _actions(cls, obj, request):
        return cls.core.get_list_actions(request, obj)

    @classmethod
    def _class_names(cls, obj, request):
        return cls.core.get_rest_obj_class_names(request, obj)

    def get_queryset(self, request):
        return self.core.get_queryset(request)

    def _filter_queryset(self, request, qs):
        filter_terms = request.GET.dict()
        for filter_temr, filter_val in filter_terms.items():
            filter = get_model_field_or_method_filter(filter_temr, self.model, filter_val)
            qs = filter.filter_queryset(qs)
        return qs

    def _order_by(self, request, qs, order_field):
        dir = request.META.get('HTTP_X_DIRECTION', 'ASC')

        if dir.upper() == 'DESC':
            order_field = '-' + order_field
        return qs.order_by(order_field)

    def _order_queryset(self, request, qs):
        if not 'HTTP_X_ORDER' in request.META:
            return qs
        order_field = request.META.get('HTTP_X_ORDER')
        if order_field in get_model_field_names(self.model):
            return self._order_by(request, qs, order_field)
        else:
            raise RestException(_('Cannot resolve X-Order value "%s" into field') % order_field)

    def read(self, request, pk=None):
        qs = self.get_queryset(request)
        if pk:
            try:
                return qs.get(pk=pk)
            except ObjectDoesNotExist:
                return rc.NOT_FOUND

        try:
            qs = self._filter_queryset(request, qs)
            qs = self._order_queryset(request, qs)
            paginator = Paginator(qs, request)
            return HeadersResult(paginator.page_qs, {'X-Total': paginator.total})
        except RestException as ex:
            return RestErrorResponse(ex.errors)
        # Filter exceptions returns empty list
        except (InterfaceError, DatabaseError, FilterException, ValueError)  as ex:
            return HeadersResult(self.model.objects.none(), {'X-Total': 0})

    def get_exclude(self, request, obj=None):
        return self.core.get_rest_form_exclude(request, obj)

    def get_fields(self, request, obj=None):
        return self.core.get_rest_form_fields(request, obj)

    def get_form_class(self, request, obj=None):
        return self.form_class or self.core.get_rest_form_class(request, obj)

    # TODO: duplicate, this is too inside DefaultFormView
    def generate_form_class(self, request, inst, exclude=[]):
        exclude = list(self.get_exclude(request, inst)) + exclude
        form_class = self.get_form_class(request, inst)
        fields = self.get_fields(request, inst)

        if hasattr(form_class, '_meta') and form_class._meta.exclude:
            exclude.extend(form_class._meta.exclude)
        return modelform_factory(self.model, form=form_class, exclude=exclude, fields=fields)

    def get_form(self, request, fields=None, inst=None, data=None, initial={}):
        # When is send PUT (resource instance exists), it is possible send only changed values.
        exclude = []

        if data and inst and fields:
            for field_name in fields:
                if field_name not in data.keys():
                    exclude.append(field_name)

        kwargs = {}
        if inst:
            kwargs['instance'] = inst
        if data:
            kwargs['data'] = data

        form_class = self.generate_form_class(request, inst, exclude)
        form = form_class(initial=initial, **kwargs)
        return form

    def validation(self, form):
        """
        Validate input data. It uses django forms
        """
        errors = {}
        if not form.is_valid():
            errors = dict([(k, v[0]) for k, v in form.errors.items()])

        non_field_errors = form.non_field_errors()
        if non_field_errors:
            errors = {'non-field-errors': non_field_errors}

        if errors:
            return errors

        return False

    def _get_instance(self, request, data):
        # If data contains id this method is update otherwise create
        inst = None
        if 'id' in data.keys():
            try:
                inst = self.get_queryset(request).get(pk=data.get('id'))
            except ObjectDoesNotExist:
                raise ResourceNotFoundException
        return inst

    def _create_or_update(self, request, data):
        """
        Helper for creating or updating resource
        """
        inst = self._get_instance(request, data)

        if inst and not self.has_update_permission(request, inst.pk):
            return inst
        elif not inst and not self.has_create_permission(request):
            raise NotAllowedException

        change = inst and True or False

        if not inst and 'POST' not in self.allowed_methods:
            raise ResourceNotFoundException

        form_fields = self.get_form(request, data=data, initial={'_user': request.user}).fields
        preprocesor = DataPreprocessor(request, self.model, form_fields, inst)
        data = preprocesor.process_data(data)

        form = self.get_form(request, fields=form_fields.keys(), inst=inst, data=data, initial={'_user': request.user})
        errors = form.is_invalid()
        if errors:
            raise DataInvalidException(errors)

        inst = form.save(commit=False)

        # Core view can do modifications before save object
        self.core.pre_save_model(request, inst, form, change)

        # Core view should save object
        self.core.save_model(request, inst, form, change)
        if hasattr(form, 'save_m2m'):
            form.save_m2m()

        # Core view event after save object
        self.core.post_save_model(request, inst, form, change)

        postprocesor = DataPostprocessor(request, self.model, form_fields, inst)
        data = postprocesor.process_data(data)

        return inst

    def _delete(self, request, inst):
        self.core.pre_delete_model(request, inst)
        self.core.delete_model(request, inst)
        self.core.post_delete_model(request, inst)

    @transaction.atomic
    def _atomic_create_or_update(self, request, data):
        inst = self._create_or_update(request, data)
        return inst

    def create(self, request, pk=None):
        if not request.data:
            return rc.BAD_REQUEST

        data = self.flatten_dict(request.data)
        try:
            inst = self._atomic_create_or_update(request, data)
        except DataInvalidException as ex:
            return HeadersResult({'errors': ex.errors}, status_code=400)
        except ResourceNotFoundException:
            # It cannot happend
            return rc.NOT_FOUND

        return HeadersResult(inst, status_code=201)

    def update(self, request, pk=None):
        if not request.data:
            return rc.BAD_REQUEST

        data = self.flatten_dict(request.data)
        data['id'] = pk
        try:
            return self._atomic_create_or_update(request, data)
        except DataInvalidException as ex:
            return HeadersResult({'errors': ex.errors}, status_code=400)
        except ResourceNotFoundException:
            return rc.NOT_FOUND

    def delete(self, request, pk):
        qs = self.get_queryset(request)

        try:
            inst = qs.get(pk=pk)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND
        self._delete(request, inst)
        return rc.DELETED
