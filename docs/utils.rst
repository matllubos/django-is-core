
Utils
=====

.. function:: render_model_object_with_link(request, obj, display_value=None)

Returns clickable text representation of a model object, which leads to its detail. It can be for example used in model's property to display clickable name of a related object in detail view. Set ``display_value`` to override model's default text representation.

.. function:: is_core.utils.get_link_or_none

Helper that generates URL from pattern name and kwargs and checks if current request has permission to open the URL, if permission is not granted None is returned.
