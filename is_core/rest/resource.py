from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import modelform_factory, ModelMultipleChoiceField
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor, SingleRelatedObjectDescriptor
from django.db import transaction
from django.db.utils import InterfaceError, DatabaseError

from piston.resource import BaseResource, BaseModelResource
from piston.utils import get_resource_of_model, rc, HeadersResult

from is_core.utils.models import get_model_field_names, get_object_or_none
from is_core.rest.paginator import Paginator
from is_core.filters import get_model_field_or_method_filter
from is_core.filters.exceptions import FilterException


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


class ConflictException(RestException):
    message = _('Object already exists but you do not allowed to change it.')


class DataProcessor(object):
    def __init__(self, request, model, form_fields, inst, via):
        self.model = model
        self.request = request
        self.form_fields = form_fields
        self.inst = inst
        self.via = via

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

    def _add_data_items_to_list(self, resource, data, list_items, errors):
        i = 1
        for data_item in data:
            if isinstance(data_item, dict):
                try:
                    list_items.append(resource._create_or_update(self.request, data_item, self.via).pk)
                except (DataInvalidException, RestException) as ex:
                    er = ex.errors
                    er.update({'_index': i})
                    errors.append(er)
            else:
                list_items.append(data_item)

    def _remove_data_items_from_list(self, resource, data, list_items, errors):
        i = 1
        for data_item in data:
            if isinstance(data_item, dict):
                if data_item.has_key(self.model._meta.pk.name):
                    if data_item.get(self.model._meta.pk.name) in list_items:
                        list_items.remove(data_item.get(self.model._meta.pk.name))
                else:
                    errors.append({'_index': i, 'error': _('Removed element must contain pk')})
            else:
                if data_item in list_items:
                    list_items.remove(data_item)
            i += 1

    def _process_list_field(self, resource, data, key, data_items, rel_model):
        """
        Set ManyToMany field
        """

        if isinstance(data_items, dict):
            data[key] = list(getattr(self.inst, key).all().values_list('pk', flat=True))
            errors = {}
            add_errors = []
            remove_errors = []
            self._add_data_items_to_list(resource, data_items.get('add', []), data[key], add_errors)
            self._remove_data_items_from_list(resource, data_items.get('remove', []), data[key], remove_errors)
            if add_errors:
                errors['add'] = add_errors
            if remove_errors:
                errors['remove'] = remove_errors

        else:
            errors = []
            data[key] = []
            self._add_data_items_to_list(resource, data_items, data[key], errors)

        if errors:
            self.errors[key] = errors

    def _process_dict_field(self, resource, data, key, data_item, rel_model):
        """
        Create or update ForeignKey field
        """
        try:
            data[key] = resource._create_or_update(self.request, data_item, self.via).pk
        except (DataInvalidException, RestException) as ex:
            self.errors[key] = ex.errors

    def _process_field(self, data, key, data_item):
        if isinstance(data_item, (list, tuple, dict)) and key in self.form_fields.keys() and\
            hasattr(self.form_fields.get(key), 'queryset'):
            rel_model = self.form_fields.get(key).queryset.model
            resource_class = get_resource_of_model(rel_model)
            if resource_class:
                resource = resource_class()

                if isinstance(self.form_fields.get(key), ModelMultipleChoiceField):
                    self._process_list_field(resource, data, key, data_item, rel_model)
                else:
                    self._process_dict_field(resource, data, key, data_item, rel_model)

    def clear_data(self, data):
        return data


class DataPostprocessor(DataProcessor):

    def _add_related_items(self, resource, data, list_items, errors, related_obj):
        i = 1
        for rel_obj_data in data:
            if not isinstance(rel_obj_data, dict):
                rel_obj_data = {related_obj.model._meta.pk.name: rel_obj_data}

            rel_obj_data[related_obj.field.name] = self.inst.pk
            try:
                list_items.append(resource._create_or_update(self.request, rel_obj_data, self.via).pk)
            except (DataInvalidException, RestException) as ex:
                er = ex.errors
                er.update({'_index': i})
                errors.append(er)
            except TypeError:
                errors.append({'error': _('Field must contains object'), '_index': i})
            i += 1

    # TODO: Throw exception if object does not exists or user has not permissions
    def _remove_related_items(self, resource, data, list_items, errors):
        i = 1
        for data_item in data:
            if isinstance(data_item, dict):
                if data_item.has_key(self.model._meta.pk.name):
                    if data_item.get(self.model._meta.pk.name) in list_items:
                        list_items.remove(data_item.get(self.model._meta.pk.name))
                else:
                    errors.append({'_index': i, 'error': _('Removed element must contain pk')})
            else:
                if data_item in list_items:
                    list_items.remove(data_item)
            i += 1

    def _remove_other_related_objects(self, resource, related_obj, existing_related):
        for reverse_related_obj in resource.model.objects.filter(**{related_obj.field.name: self.inst})\
                                    .exclude(pk__in=existing_related):
            if resource.has_delete_permission(self.request, reverse_related_obj, self.via):
                resource._delete(self.request, reverse_related_obj)


    def _process_dict_field(self, resource, data, key, data_item, related_obj):
        related_model_obj = get_object_or_none(related_obj.model, **{related_obj.field.name:self.inst.pk})

        if data_item is None and related_model_obj:
            if resource.has_delete_permission(self.request, related_model_obj, self.via):
                resource._delete(self.request, related_model_obj)
            else:
                self.errors[key] = {'error': _('You don not have permisson to delete object')}
        else:
            try:
                data_item[related_obj.field.name] = self.inst.pk

                # Update OneToOne field without pk
                if related_model_obj:
                    data_item[related_obj.model._meta.pk.name] = related_model_obj.pk

                data[key] = resource._create_or_update(self.request, data_item, self.via).pk
            except (DataInvalidException, ResourceNotFoundException) as ex:
                self.errors[key] = ex.errors
            except TypeError:
                self.errors[key] = {'error': _('Field must contains object')}

    def _process_list_field(self, resource, data, key, data_items, related_obj):
        """
        Create or update reverse ForeignKey field
        """

        if isinstance(data_items, dict):
            existing_related = list(resource.model.objects.filter(**{related_obj.field.name: self.inst}).values_list('pk', flat=True))
            errors = {}
            add_errors = []
            remove_errors = []

            self._add_related_items(resource, data_items.get('add', []), existing_related, add_errors, related_obj)
            self._remove_related_items(resource, data_items.get('remove', []), existing_related, remove_errors)
            if add_errors:
                errors['add'] = add_errors
            if remove_errors:
                errors['remove'] = remove_errors
        else:
            errors = []
            existing_related = []
            self._add_related_items(resource, data_items, existing_related, errors, related_obj)

        self._remove_other_related_objects(resource, related_obj, existing_related)

        if errors:
            self.errors[key] = errors

    def _process_field(self, data, key, data_item):
        if key not in self.form_fields.keys() and hasattr(self.model, key):
            if isinstance(getattr(self.model, key), ForeignRelatedObjectsDescriptor):
                related_obj = getattr(self.model, key).related
                resource_class = get_resource_of_model(related_obj.model)
                if resource_class:
                    self._process_list_field(resource_class(), data, key, data_item, related_obj)
            elif isinstance(getattr(self.model, key), SingleRelatedObjectDescriptor):
                related_obj = getattr(self.model, key).related
                resource_class = get_resource_of_model(related_obj.model)
                if resource_class:
                    self._process_dict_field(resource_class(), data, key, data_item, related_obj)


class RestResource(BaseResource):
    login_required = True

    def dispatch(self, request, *args, **kwargs):
        if hasattr(self, 'core'):
            self.core.init_rest_request(request)
        return super(RestResource, self).dispatch(request, *args, **kwargs)

    @classmethod
    def __init_core__(cls, core, pattern):
        cls.core = core
        cls.pattern = pattern

    @classmethod
    def as_wrapped_view(cls, wrapper_class, allowed_methods, **initkwargs):
        wrapper = cls.as_view(**initkwargs)

        auth_wrapper = wrapper_class(cls.get_permission_validators(allowed_methods),
                                     **initkwargs).wrap(wrapper)
        auth_wrapper.csrf_exempt = wrapper.csrf_exempt
        return auth_wrapper


class RestCoreResourceMixin(object):

    @classmethod
    def has_read_permission(cls, request, obj=None, via=None):
        return super(RestCoreResourceMixin, cls).has_read_permission(request, obj) \
                and cls.core.has_rest_read_permission(request, obj, via)

    @classmethod
    def has_create_permission(cls, request, obj=None, via=None):
        return super(RestCoreResourceMixin, cls).has_create_permission(request, obj) \
                and cls.core.has_rest_create_permission(request, obj, via)

    @classmethod
    def has_update_permission(cls, request, obj=None, via=None):
        return super(RestCoreResourceMixin, cls).has_update_permission(request, obj) \
                and cls.core.has_rest_update_permission(request, obj, via)

    @classmethod
    def has_delete_permission(cls, request, obj=None, via=None):
        return super(RestCoreResourceMixin, cls).has_delete_permission(request, obj) \
                and cls.core.has_rest_delete_permission(request, obj, via)


class RestModelResource(RestResource, RestCoreResourceMixin, BaseModelResource):

    fields = ('_rest_links', '_actions', '_class_names', '_obj_name')
    default_obj_fields = ('_rest_links', '_obj_name')
    default_list_fields = ('_rest_links', '_obj_name')
    register = False
    form_class = None

    def get_fields(self, request, obj):
        return self.core.get_rest_fields(request, obj=obj)

    def get_default_obj_fields(self, request, obj):
        return self.core.get_rest_obj_fields(request, obj=obj)

    def get_default_list_fields(self, request):
        return self.core.get_rest_list_fields(request)

    def get_guest_fields(self, request):
        return self.core.get_rest_guest_fields(request)

    @classmethod
    def _web_links(cls, obj, request):
        web_links = {}
        for pattern in cls.core.web_link_patterns(request):
            url = pattern.get_url_string(request, obj=obj)
            if url:
                web_links[pattern.name] = url
        return web_links

    @classmethod
    def _rest_links(cls, obj, request):
        rest_links = {}
        for pattern in cls.core.resource_patterns.values():
            url = pattern.get_url_string(request, obj=obj)
            if url:
                allowed_methods = pattern.get_allowed_methods(request, obj)
                if allowed_methods:
                    rest_links[pattern.name] = {'url': url, 'methods': pattern.get_allowed_methods(request, obj)}
        return rest_links

    @classmethod
    def _default_action(cls, obj, request):
        return cls.core.get_default_action(request, obj=obj)

    @classmethod
    def _actions(cls, obj, request):
        ac = cls.core.get_list_actions(request, obj)
        return ac

    @classmethod
    def _class_names(cls, obj, request):
        return cls.core.get_rest_obj_class_names(request, obj)

    def get_queryset(self, request):
        return self.core.get_queryset(request)

    def _filter_queryset(self, request, qs):
        filter_terms = request.GET.dict()
        for filter_temr, filter_val in filter_terms.items():
            filter = get_model_field_or_method_filter(filter_temr, self.model, filter_val)
            qs = filter.filter_queryset(qs, request)
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

    def read(self, request, pk=None, **kwargs):
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
            return RestErrorResponse(ex.message)
        # Filter exceptions returns empty list
        except (InterfaceError, DatabaseError, FilterException, ValueError)  as ex:
            return HeadersResult(self.model.objects.none(), {'X-Total': 0})

    def get_exclude(self, request, obj=None):
        return self.core.get_rest_form_exclude(request, obj)

    def get_rest_form_fields(self, request, obj=None):
        return self.core.get_rest_form_fields(request, obj)

    def get_form_class(self, request, obj=None):
        return self.form_class or self.core.get_rest_form_class(request, obj)

    # TODO: duplicate, this is too inside DefaultFormView
    def generate_form_class(self, request, inst, exclude=[]):
        exclude = list(self.get_exclude(request, inst)) + exclude
        form_class = self.get_form_class(request, inst)
        fields = self.get_rest_form_fields(request, inst)

        if hasattr(form_class, '_meta') and form_class._meta.exclude:
            exclude.extend(form_class._meta.exclude)
        return modelform_factory(self.model, form=form_class, exclude=exclude, fields=fields)

    def get_form(self, request, fields=None, inst=None, data=None, initial={}):
        # When is send PUT (resource instance exists), it is possible send only changed values.
        exclude = []

        kwargs = {}
        if inst:
            kwargs['instance'] = inst
        if data:
            kwargs['data'] = data
            kwargs['files'] = request.FILES

        form_class = self.generate_form_class(request, inst, exclude)
        form = form_class(initial=initial, **kwargs)
        return form

    def _get_instance(self, request, data):
        # If data contains id this method is update otherwise create
        inst = None
        if self.model._meta.pk.name in data.keys():
            try:
                inst = self.get_queryset(request).get(pk=data.get(self.model._meta.pk.name))
            except ObjectDoesNotExist:
                if self.model.objects.filter(pk=data.get(self.model._meta.pk.name)).exists():
                    raise ConflictException
        return inst

    def _create_or_update(self, request, data, via=None):
        """
        Helper for creating or updating resource
        """

        if via is None:
            via = []

        inst = self._get_instance(request, data)

        if inst and not self.has_update_permission(request, inst, via):
            return inst
        elif not inst and not self.has_create_permission(request, via=via):
            raise NotAllowedException

        change = inst and True or False

        form_fields = self.get_form(request, inst=inst, data=data, initial={'_user': request.user,
                                                                            '_request': request}).fields
        preprocesor = DataPreprocessor(request, self.model, form_fields, inst, via + [self])
        data = preprocesor.process_data(data)
        form = self.get_form(request, fields=form_fields.keys(), inst=inst, data=data, initial={'_user': request.user,
                                                                                                '_request': request})

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
        postprocesor = DataPostprocessor(request, self.model, form_fields, inst, via + [self])
        data = postprocesor.process_data(data)

        self.core.post_save_model(request, inst, form, change)
        return inst

    def _delete(self, request, inst):
        self.core.pre_delete_model(request, inst)
        self.core.delete_model(request, inst)
        self.core.post_delete_model(request, inst)

    @transaction.atomic
    def _atomic_create_or_update(self, request, data):
        inst = self._create_or_update(request, data)
        return inst

    def _prepare_data(self, request):
        data = self.flatten_dict(request.data)
        return data

    def create(self, request, pk=None, **kwargs):
        data = self._prepare_data(request)
        if data.has_key(self.model._meta.pk.name) and self.model.objects.filter(pk=data.get(self.model._meta.pk.name))\
            .exists():
            return rc.DUPLICATE_ENTRY

        try:
            inst = self._atomic_create_or_update(request, data)
        except DataInvalidException as ex:
            return HeadersResult({'errors': ex.errors}, status_code=400)
        except ResourceNotFoundException:
            # It cannot happend
            return rc.NOT_FOUND
        except RestException as ex:
            return RestErrorResponse(ex.message)

        return HeadersResult(inst, status_code=201)

    def update(self, request, pk=None, **kwargs):
        data = self._prepare_data(request)
        data[self.model._meta.pk.name] = pk
        try:
            return self._atomic_create_or_update(request, data)
        except DataInvalidException as ex:
            return HeadersResult({'errors': ex.errors}, status_code=400)
        except ResourceNotFoundException:
            return rc.NOT_FOUND
        except ConflictException as ex:
            return rc.FORBIDDEN
        except RestException as ex:
            return RestErrorResponse(ex.message)

    def delete(self, request, pk, **kwargs):
        qs = self.get_queryset(request)

        try:
            inst = qs.get(pk=pk)
        except ObjectDoesNotExist:
            return rc.NOT_FOUND
        self._delete(request, inst)
        return rc.DELETED
