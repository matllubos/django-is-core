
Utils
=====

.. function:: render_model_object_with_link(request, obj, display_value=None)

Returns clickable text representation of a model object, which leads to its detail. It can be for example used in model's property to display clickable name of a related object in detail view. Set ``display_value`` to override model's default text representation.

.. function:: render_model_objects_with_link(request, objs)

The function generates humanized value from objects. The value should be link to the object detail if the URL exists and the request user has permissions to see it.

.. function:: is_core.utils.get_link_or_none(pattern_name, request, view_kwargs=None)

Helper that generates URL from pattern name and kwargs and checks if current request has permission to open the URL, if permission is not granted None is returned.

.. function:: is_core.utils.display_for_value(value, request=None)

Returns humanized format of the input value. Input value can be model object, list, dict, number, boolean, datetime, etc.

.. function:: is_core.utils.display_json(value)

Returns humanized value of the input json string.

.. function:: is_core.utils.display_code(value)

Gets the humanized value for input code. The string value spaces are kept in the result HTML.