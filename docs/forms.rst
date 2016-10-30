Forms
=====

``is_core.forms`` contains helpers for forms rutines. The most interesting class is ``SmartForm``.

SmartForm
---------
Imagine you need to dynamically change behaviour of your form fields, e.g. make a field required when some
condition holds. In pure Django, you would override the ``__init__`` method and change the field attributes there.
However, that's pretty uncomfortable as you need to explicitly call super. More importantly, the ``__init__`` method
tends to grow and become unreadable for complex forms. With ``SmartForm``, you can define ``_init_fields`` method
instead and put your field-related logic there. For example::

    from is_core.forms import SmartForm

    class MyForm(SmartForm):

        def _init_fields(self):

            for field in self.fields:
                if field.name == 'foo':
                    # do logic for foo
                elif field.name == 'bar':
                    # do logic for bar


Even more readable way is to define the ``_init_{field_name}`` method for the individual fields thus removing
the clumsy for cycle and if-elif-else::

    from is_core.forms import SmartForm

    class MyForm(SmartForm):

        def _init_foo(self, field):
            field.required = False
            if self._my_secret_condition():
                # do logic for foo

        def _init_bar(self, field):
            # do logic for bar

Yay! It's pretty, isn't it?


``SmartForm`` contains helper methods that are called when an instance is created in a following order:

1. ``_pre_init_fields``
2. ``_init_{field_name}`` methods
3. ``_init_fields``

.. method:: SmartForm._pre_init_fields(self)

This method is called when a form is created (after super ``__init__`` method and before ``_init_{field_name}`` methods).
It makes fields from ``base_required_fields`` attribute required.


.. method:: SmartForm._init_{field_name}(self, field)

This method is called when a form has **foo** field and it is created (after super ``__init__`` method and after
``_pre_init_fields`` method). You can modify the field's attributes here. There is no need to return
the field as it modifies the internal state of the passed field.::

    from is_core.forms import SmartForm


    class MyForm(SmartForm):

        def _init_foo(field):
            # put logic here


.. method:: SmartForm._init_fields(self)

This method is called when a form is created (after super ``__init__`` method and after ``_init_{field_name}`` methods::

    from is_core.forms import SmartForm


    class MyForm(SmartForm):

        def _init_fields(self):
            # put logic here


.. attribute:: SmartForm.changed_data

This attribute contains changed data as a ``dict``. `More details. <https://docs.djangoproject.com/en/1.8/ref/forms/api/#django.forms.Form.changed_data>`_


SmartFormMixin
--------------

In case that you have your own form you can use this mixin to get same functionality as ``SmartForm``.

.. function:: smartform_factory(request, form, readonly_fields=None, required_fields=None,
                                exclude=None, formreadonlyfield_callback=None, readonly=False)

A wrapper factory for ``SmartForm``.
