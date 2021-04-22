import types

from django.db.models import Model, QuerySet, Field

from chamber.utils import get_class_method, call_function_with_unknown_input, InvalidFunctionArguments

from pyston.serializer import get_resource_class_or_none

from is_core.forms.utils import ReadonlyValue
from is_core.forms.widgets import ReadonlyWidget, ManyToManyReadonlyWidget, ModelObjectReadonlyWidget
from is_core.utils import LOOKUP_SEP, get_field_from_model_or_none


class GetFieldDescriptorException(Exception):
    pass


class FieldDoesNotExist(GetFieldDescriptorException):
    pass


class FieldIsNotRelation(GetFieldDescriptorException):
    pass


class GetFieldDescriptorValueError(GetFieldDescriptorException):
    pass


def pretty_name(value):
    return value.replace('_', ' ')


class FieldDescriptor:

    is_method = False
    is_model_field = False
    is_property = False

    def __init__(self, model, field_name, model_field_or_method):
        self.model = model
        self.field_name = field_name
        self.model_field_or_method = model_field_or_method

    def get_related_model(self):
        related_model = getattr(self.model_field_or_method, 'related_model', None)
        if related_model:
            return related_model
        else:
            raise FieldIsNotRelation('Model ("{}") field ("{}") with name "{}" is not relation'.format(
                self.model, self.model_field_or_method, self.field_name
            ))

    def get_label(self):
        raise NotImplementedError

    def get_widget(self):
        return ReadonlyWidget

    def get_value(self, instance, request=None):
        raise NotImplementedError

    def _get_verbose_value(self, raw, instance):
        if hasattr(self.model_field_or_method, 'humanized') and self.model_field_or_method.humanized:
            return self.model_field_or_method.humanized(raw, instance)
        elif (hasattr(self.model_field_or_method, 'attname')
                  and hasattr(instance, 'get_{}_display'.format(self.model_field_or_method.attname))):
            return getattr(instance, 'get_{}_display'.format(self.model_field_or_method.attname))()
        else:
            return None

    def get_readonly_value(self, instance, request=None):
        value = self.get_value(instance, request)
        verbose_value = self._get_verbose_value(value, instance)
        return ReadonlyValue(value, verbose_value) if verbose_value is not None else value


class ModelFieldDescriptor(FieldDescriptor):
    """
    Field descriptor which gets field data from Django model field.
    """

    is_model_field = True

    def get_label(self):
        if self.model_field_or_method.auto_created and self.model_field_or_method.is_relation:
            return self.model_field_or_method.field.reverse_verbose_name
        elif hasattr(self.model_field_or_method, 'verbose_name'):
            return self.model_field_or_method.verbose_name
        else:
            return pretty_name(self.field_name)

    def get_widget(self):
        field = self.model_field_or_method

        if field.auto_created and (field.one_to_many or field.many_to_many):
            return ManyToManyReadonlyWidget
        elif field.auto_created and field.one_to_one:
            return ModelObjectReadonlyWidget
        elif isinstance(field, Field):
            form_field =  field.formfield()
            return form_field.readonly_widget if form_field else ReadonlyWidget
        else:
            # GenericForeignKey is model field without formfield method
            return ReadonlyWidget

    def get_value(self, instance, request=None):
        field = self.model_field_or_method
        if (field.auto_created and field.one_to_many) or field.many_to_many:
            return [obj for obj in getattr(instance, field.name).all()]
        elif field.auto_created and field.one_to_one:
            return None if not hasattr(instance, field.name) else getattr(instance, field.name)
        else:
            return getattr(instance, field.name) if hasattr(instance, field.name) else None


class MethodOrPropertyDescriptor(FieldDescriptor):
    """
    Field descriptor which gets field data from object method or property.
    """

    def get_label(self):
        return getattr(self.model_field_or_method, 'short_description', pretty_name(self.field_name))

    def _get_field_or_method_value(self, instance, request=None):
        raise NotImplementedError

    def _clean_value(self, value):
        related_model = getattr(self.model_field_or_method, 'related_model', None)
        if value is not None and related_model:
            if isinstance(value, (QuerySet, list, tuple, set, types.GeneratorType)):
                if any(not isinstance(v, related_model) for v in value):
                    raise GetFieldDescriptorValueError(
                        'Method "{}" not returned related model ({}) value or its iterable'.format(
                            self.model_field_or_method, related_model
                        )
                    )
                return list(value)
            elif not isinstance(value, related_model):
                raise GetFieldDescriptorValueError(
                    'Method "{}" not returned related model ({}) value or its iterable'.format(
                        self.model_field_or_method, related_model
                    )
                )
        return value

    def get_value(self,instance, request=None):
        return self._clean_value(self._get_field_or_method_value(instance, request))


class PropertyDescriptor(MethodOrPropertyDescriptor):
    """
    Field descriptor which gets field data from object property.
    """

    is_property = True

    def _get_field_or_method_value(self, instance, request=None):
        return getattr(instance, self.field_name)


class BaseModelMethodDescriptor(MethodOrPropertyDescriptor):
    """
    Field descriptor which gets field data from object method.
    """

    is_method = True

    def _get_field_or_method_value(self, instance, request=None):
        return call_function_with_unknown_input(
            self.model_field_or_method, **self._get_method_kwargs(instance, request)
        )

    def _get_method_kwargs(self, instance, request=None):
        if request:
            return {'obj': instance, 'request': request}
        else:
            return {'obj': instance}


class ModelMethodDescriptor(BaseModelMethodDescriptor):
    """
    Field descriptor which gets field data from Django model method.
    """

    def _get_method_kwargs(self, instance, request=None):
        return {
            'self': instance,
            **super()._get_method_kwargs(instance, request)
        }


class ResourceMethodDescriptor(BaseModelMethodDescriptor):
    """
    Field descriptor which gets field data from Django model resource method.
    """

    def __init__(self, model, field_name, method, resource_class):
        super().__init__(model, field_name, method)
        self.resource_class = resource_class

    def _get_method_kwargs(self, instance, request=None):
        if request is None:
            raise InvalidFunctionArguments('For resource method "{}" value is required request'.format(self.field_name))

        return {
            'self': self.resource_class(request),
            **super()._get_method_kwargs(instance, request)
        }


class ViewMethodDescriptor(BaseModelMethodDescriptor):
    """
    Field descriptor which gets field data from core view method.
    """

    def __init__(self, model, field_name, method, view):
        super().__init__(model, field_name, method)
        self.view = view

    def _get_method_kwargs(self, instance, request=None):
        return {
            'self': self.view,
            **super()._get_method_kwargs(instance, request)
        }


def _get_field_descriptor_from_model(model, field_name):
    """
    Return model field od model method or raise FieldDoesNotExist exception
    """
    from is_core.site import get_model_core

    resource = get_resource_class_or_none(model)

    if resource:
        resource_method = resource.get_method_returning_field_value(field_name)
        if resource_method:
            return ResourceMethodDescriptor(model, field_name, resource_method, resource)

    field = get_field_from_model_or_none(model, field_name)
    if field:
        return ModelFieldDescriptor(model, field_name, field)

    method = get_class_method(model, field_name)
    if method:
        return ModelMethodDescriptor(model, field_name, method)

    property = getattr(model, field_name, None)
    if property:
        return PropertyDescriptor(model, field_name, property)

    raise FieldDoesNotExist('Model ("{}") field with name "{}" was not found'.format(model, field_name))


def _get_field_descriptor_from_view(model, view, field_name):
    view_method = view.get_method_returning_field_value(field_name)
    if view_method:
        return ViewMethodDescriptor(model, field_name, view_method, view)
    else:
        return None


def _get_field_descriptor(model, field_name, view=None):
    if view:
        descriptor = _get_field_descriptor_from_view(model, view, field_name)
        if descriptor:
            return descriptor

    return _get_field_descriptor_from_model(model, field_name)


def get_field_descriptors_from_path(model, field_path, view=None):
    """
    Helper returns list of field descriptors. Input field_path is consist of field names separated with "__".
    For every field name is found the right descriptor which describes how to get field label, value or
    how to humanize this value. There are 5 types of field descriptors:

    * ModelFieldDescriptor - value and label is get from django model field
    * PropertyDescriptor - value is get from instance property
    * ModelMethodDescriptor - value will be obtained as a result of model method call.
    * ResourceMethodDescriptor - firstly is found pyston resource of model. The result value is get from resource
                                 method.  Because resource is related with core. The method will be searching
                                 in the core too.
    * ViewMethodDescriptor - if view is in the input parameters. Descriptor can be get from view method too.

    :param model: Django model class.
    :param field_path: field names separated with __.
    :param view: view instance.
    :return: list of FieldDescriptor or GetFieldDescriptorException is raised
    """
    try:
        if LOOKUP_SEP in field_path:
            current_field_name, next_field_path = field_path.split(LOOKUP_SEP, 1)
            field_descriptor = _get_field_descriptor(model, current_field_name, view)
            return [field_descriptor] + get_field_descriptors_from_path(
                field_descriptor.get_related_model(), next_field_path
            )
        else:
            return [_get_field_descriptor(model, field_path, view)]
    except (GetFieldDescriptorException, InvalidFunctionArguments) as ex:
        raise GetFieldDescriptorException('Field path "{}" cannot be get from model "{}". Reason: {}'.format(
            field_path,
            model,
            ex
        ))


def get_field_value_from_path(instance, field_path, request=None, view=None, return_readonly_value=False):
    """
    Return value from model instance defined by field_path. Path can contain relations defined via "__" separator.
    :param instance: django model instance.
    :param field_path: field path where field can be relations separated with "__"-
    :param request: django HTTP request
    :param view: django view which can contains method with field value.
    :param return_readonly_value: value can be automatically humanized if value is set to True.
    :return: model field path value or GetFieldDescriptorException
    """

    field_descriptors = get_field_descriptors_from_path(instance.__class__, field_path, view)
    field_descriptor = field_descriptors[0]
    try:
        if len(field_descriptors) > 1:
            value = field_descriptor.get_value(instance, request)
            if value is None:
                return value
            elif isinstance(value, list):
                return [
                    get_field_value_from_path(
                        v, field_path.split(LOOKUP_SEP, 1)[1], request, return_readonly_value=return_readonly_value
                    )
                    for v in value
                ]
            else:
                return get_field_value_from_path(
                    value, field_path.split(LOOKUP_SEP, 1)[1], request, return_readonly_value=return_readonly_value
                )
        else:
            if return_readonly_value:
                return field_descriptor.get_readonly_value(instance, request)
            else:
                return field_descriptor.get_value(instance, request)
    except (GetFieldDescriptorValueError, InvalidFunctionArguments) as ex:
        raise GetFieldDescriptorValueError('Value cannot be get from field path "{}" of model "{}". Reason: {}'.format(
            field_path,
            instance.__class__,
            ex
        ))
