
Cores
=====

UIRESTModelISCore
-----------------

The purpose of ``ISCore`` is to get a shared functionality of views into a one source.
The ``UIRESTModelISCore`` class is the representation of a model in the **django-is-core** interface. These
representations are stored in a file named ``cores.py`` in your application. We will start with the most common case when
you want to create three typical views for information system:

  * table view for printing objects
  * view for creating new objects
  * view for editing objects

As example project we use Issue tracker. Firstly for every application you need management of users. We use default
**Django** user model.

For creating **add**, **edit** and **table** views you must only create file ``cores.py`` inside specific application that
contains::

    from django.contrib.auth.models import User

    from is_core.main import UIRESTModelISCore

    class UserISCore(UIRESTModelISCore):
        model = User

There is no obligation for registration. Cores are registered automatically. The result views with preview are:

Table/List
^^^^^^^^^^
image 1


Add
^^^
image 2


Edit
^^^^
image 3


REST
^^^^
But there is created REST resource too. By default on URLs ``/api/user/`` and ``/api/user/{obj_id}`` that returns 
object in asked format (HTTP header ``Content-type: application/json``).



RESTModelISCore
----------------

The ``RESTModelISCore`` is parent of ``UIRESTModelISCore``. As the name suggests this class is used only for creating
REST resources without UI HTML views. The usage is the same as ``UIRESTModelISCore``::

    from django.contrib.auth.models import User

    from is_core.main import RESTModelISCore

    class RESTUserISCore(RESTModelISCore):
        model = User


UIModelISCore
-------------

The ``UIModelISCore`` is the second parent of ``UIRESTModelISCore``. It is used for creating only UI views. Because UI
views needs some REST resources is necessary to specify on which URL is deployed REST resource of model (api_url_name is
transformed to URL by Django resolve helper)::

    from django.contrib.auth.models import User

    from is_core.main import UIModelISCore

    class UIUserISCore(UIModelISCore):
        model = User
        api_url_name = 'api-user'


You can specify URL manually::

    class UIUserISCore(UIModelISCore):
        model = User

        def get_api_url(self, request):
            return '/api/user/'

ISCore hiearchy
---------------

Now we provide detailed description of all ISCore objects. Firstly for better understanding you can see UML class 
diagram of core hierarchy.

# TODO add diagram


ISCore
------

Following options and methods can be applied for all Core objects like ``RESTModelISCore``, ``UIModelISCore`` or
``UIRESTModelISCore`` (all descendants of ISCore class).


Options
^^^^^^^

.. attribute:: ISCore.abstract

The variable ``abstract`` provides way how to create core that is not registered but this class variable is not inherited.
Let's show an example::

    from django.contrib.auth.models import User

    from is_core.main import RESTModelISCore

    class AbstractUIRESTUserISCore(RESTModelISCore):
        model = User
        abstract = True
        verbose_name = 'example of abstract user core'

    class UIRESTUserISCore(AbstractUIRESTUserISCore):
        pass

First core is not registered. Therefore views and REST resources are not created. But the second core that inherits from
the abstract core is registered. All configuration from parent class is inhered (without abstract variable).

.. attribute:: ISCore.verbose_name,ISCore.verbose_name_plural

These variables are used inside generic views. It can be added to ``context_data`` and rendered inside templates.

.. attribute:: ISCore.menu_group

It is necessary have a slug that distinguish one core from another. For this purpose is used variable ``menu_group``.
This variable is used for example to generate URL patterns or menu. Value of the variable is generated automatically
for cores that is connected to model.

Methods
^^^^^^^

.. method:: ISCore.init_request(request)

Every core views/REST resources calls this method before calling dispatch. You can use it to change request its calling.

.. method:: ISCore.get_url_prefix()

Every core must have unique URL. Therefore a method ``get_url_prefix`` is way how to achieve it. Method defines URL
prefix for all views and rest resources. By default the URL prefix is value of attribute menu_group.

ModelISCore
-----------

The next class that extends ``ISCore`` is ``ModelISCore``. All cores that inherits from ModelISCore works
as controller over a model.

Options
^^^^^^^

.. attribute:: ModelISCore.list_actions

Variable ``list_action`` contains actions that user can perform via REST or UI. More detailed explanation with example
you find inside ``UIRESTModelISCore options`` part.

.. attribute:: ModelISCore.form_fields

Use the ``form_fields`` option to make simple layout changes in the forms on the **add** and **edit** and REST resources
pages such as showing only a subset of available fields, modifying their order, or grouping them into rows. We will
show it on ``UIRESTModelISCore``. If you want to restrict form fields to ``username``, ``first_name`` and ``last_name``
the simpliest way is use::

    from django.contrib.auth.models import User

    from is_core.main import UIRESTModelISCore

    class UserISCore(UIRESTModelISCore):
        model = User
        form_fields = ('username', 'fist_name', 'last_name')

.. attribute:: ModelISCore.form_exclude

This attribute, if given, should be a list of field names to exclude from the form.::

    from django.contrib.auth.models import User

    from is_core.main import UIRESTModelISCore

    class UserISCore(UIRESTModelISCore):
        model = User
        form_exclude = ('password',)

.. attribute:: ModelISCore.form_class

If you want to change default form class which is ``SmartModelForm`` you can change it with this option. The form is
changed for **add**, **edit** views and REST resources too.

.. attribute:: ModelISCore.ordering

Option for changing default ordering of model for core.::

    from django.contrib.auth.models import User

    from is_core.main import UIRESTModelISCore

    class UserISCore(UIRESTModelISCore):
        model = User
        ordering = ('last_name', 'fist_name', '-created_at')

Methods
^^^^^^^

.. method:: ModelISCore.get_form_fields(request, obj=None)

Use this method to define form fields dynamically or if you want to define different form fields for **add**, **edit**,
view of REST resources.


.. method:: ModelISCore.get_form_exclude(request, obj=None)

The opposite to get_form_fields.

.. method:: ModelISCore.get_form_class(request, obj=None)

Use this method to define form dynamically or if you want to define different form for **add**, **edit** view of REST 
resources.

.. method:: ModelISCore.pre_save_model(request, obj, form, change)

Method ``per_save_model`` is called before saving object to database. Body is empty by default.

.. method:: ModelISCore.post_save_model(request, obj, form, change)

Method ``post_save_model`` is called after saving object to database. Body is empty by default.

.. method:: ModelISCore.save_model(request, obj, form, change)

You can rewrite this method if you want to change way how is object saved to database. Default body is::

    def save_model(self, request, obj, form, change):
        obj.save()

.. method:: ModelISCore.pre_delete_model(request, obj)

Method ``pre_delete_model`` is called before removing object from database. Body is empty by default.

.. method:: ModelISCore.post_delete_model(request, obj)

Method ``post_delete_model`` is called after removing object from database. Body is empty by default.

.. method:: ModelISCore.delete_model(request, obj)

You can rewrite this method if you want to change way how is object removed from database. Default body is::

    def delete_model(self, request, obj):
        obj.delete()

.. method:: ModelISCore.verbose_name(),ModelISCore.verbose_name_plural()

Default verbose names of ``ModelISCore`` is get from model meta options::

    self.model._meta.verbose_name
    self.model._meta.verbose_name_plural

.. method:: ModelISCore.menu_group()

Default ``menu_group`` value is get from module name of model (``self.model._meta.module_name``)

.. method:: ModelISCore.get_ordering(request)

Use this method if you want to change ordering dynamically.

.. method:: ModelISCore.get_queryset(request)

Returns model queryset, ordered by defined ordering inside core. You can filter here objects according to user 
permissions.

.. method:: ModelISCore.preload_queryset(request, qs)

The related objects of queryset should sometimes very slow down retrieving data from the database. If you want to
improve a speed of your application use this function to create preloading of related objects.

.. method:: ModelISCore.get_list_actions(request, obj)

Use this method if you want to change ``list_actions`` dynamically.


.. method:: ModelISCore.get_default_action(request, obj)

Chose default action for object used inside UI and REST. For example default action is action that is performed if you
select row inside table of objects. For table view default action is open **edit** view. If you return ``None``
no action is performed by default.


UIISCore
--------

Options
^^^^^^^

.. attribute:: UIISCore.menu_url_name

Every UI core has one place inside menu that addresses one of UI views of a core. This view is selected by option 
``menu_url_name``.

.. attribute:: UIISCore.show_in_menu

Option `show_in_menu` is set to ``True`` by default. If you want to remove core view from menu set this option to
``False``.

.. attribute:: UIISCore.view_classes

Option contains view classes that are automatically added to Django urls. Use this option to add new views. Example 
you can see in section generic views (this is a declarative way if you want to register views dynamically see
``UIISCore.get_view_classes``).::

    from django.contrib.auth.models import User

    from is_core.main import UIRESTModelISCore

    from .views import MonthReportView


    class UserISCore(UIRESTModelISCore):
        model = User

        view_classes = (
            ('reports', r'^/reports/$', MonthReportView),
        )

.. attribute:: UIISCore.default_ui_pattern_class

Every view must have assigned is-core pattern class. This pattern is not the same patter that is used with **django**
`urls`. This pattern has higher usability. You can use it to generate the url string or checking permissions. Option
default_ui_pattern_class contains pattern class that is used with defined view classes. More about patterns you can 
find in section patterns. #TODO add link

Methods
^^^^^^^

.. method:: UIISCore.init_ui_request(request)

Every view defined with option ``view_classes`` calls this method before calling dispatch. The default implementation of
this method calls parent method ``init_request``::

    def init_ui_request(self, request):
        self.init_request(request)

.. method:: UIISCore.get_view_classes()

Use this method if you want to change ``view_classes`` dynamically. A following example shows overriding **edit** view
and registering a custom view::

    from django.contrib.auth.models import User

    from is_core.main import UIRESTModelISCore

    from .views import UserEditView, MonthReportView


    class UserISCore(UIRESTModelISCore):
        model = User

        def get_view_classes(self):
            view_classes = super(UserISCore, self).get_view_classes()
            view_classes['edit'] = (r'^/(?P<pk>\d+)/$', UserEditView)
            view_classes['reports'] = (r'^/reports/$', MonthReportView)
            return view_classes


.. method:: UIISCore.get_ui_patterns()

Contains code that generates ``ui_patterns`` from view classes. Method returns ordered dict of pattern classes.


.. method:: UIISCore.get_show_in_menu(request)

Returns ``boolean`` if menu link is provided for the core, by default there are three rules:

 * show_in_menu must be set to ``True``
 * menu_url_name need not be empty
 * current user must have permissions to see the linked view


.. method:: UIISCore.is_active_menu_item(request, active_group)

This method finds if a menu link of a core is active (if the view with ``menu_url_name`` is the current displayed page).


.. method:: UIISCore.get_menu_item(request, active_group)

This method returns a menu item object that contains information about the link displayed inside menu.

.. method:: UIISCore.menu_url(request, active_group)

Returns URL string of menu item.


RESTISCore
----------

``RESTISCore`` is very similar to ``UIISCore``, but provides REST resources instead of UI views.

Options
^^^^^^^

.. attribute:: RESTISCore.rest_classes

Option contains REST classes that are automatically added to django urls. Use this option to add new REST resources. 
Example you can see in section REST. #TODO add link

.. attribute:: RESTISCore.default_rest_pattern_class

As UI views every resource must have assigned is-core pattern class. Default pattern for REST resources is 
`RESTPattern`. More about patterns you can find in section patterns. #TODO add link

Methods
^^^^^^^

.. method:: RESTISCore.init_rest_request(request)

Every resource defined with option ``rest_classes`` calls this method before calling dispatch. The default implementation 
of this method calls parent method ``init_request``.

.. method:: RESTISCore.get_rest_classes()

Use this method if you want to change ``rest_classes`` dynamically.

.. method:: RESTISCore.get_rest_patterns()

Contains code that generates ``rest_patterns`` from rest classes. Method returns an ordered dict of pattern classes.

HomeUIISCore
------------

``HomeISCore`` contains only one UI view which is index page. By default this page is empty and contains only menu
because every information system has custom index. You can very simply change default view class by changing ``settings``
attribute ``HOME_VIEW``, the default value is::

    HOME_VIEW = 'is_core.generic_views.HomeView'

You can change whole is core too by attribute ``HOME_IS_CORE``, default value::

    HOME_IS_CORE = 'is_core.main.HomeUIISCore'


UIModelISCore
-------------

``UIModelISCore`` represents core that provides standard views for model creation, editation and listing. The 
``UIModelISCore`` will not work correctly without REST resource. Therefore you must set ``api_url_name`` option.

Options
^^^^^^^

.. attribute:: UIModelISCore.default_model_view_classes

For the ``UIModelISCore`` default views are **add**, **edit** and **list**::

    default_model_view_classes = (
        ('add', r'^/add/$', AddModelFormView),
        ('edit', r'^/(?P<pk>[-\w]+)/$', EditModelFormView),
        ('list', r'^/?$', TableView),
    )

.. attribute:: UIModelISCore.api_url_name

The ``api_url_name`` is required attribute. The value is pattern name of REST resource.

.. attribute:: UIModelISCore.list_display
 
Set ``list_display`` to control which fields are displayed on the list page.

.. attribute:: UIModelISCore.export_display

Set ``export_display`` to control which fields are displayed inside exports (e.g. PDF, CSV, XLSX).

.. attribute:: UIModelISCore.export_types

REST resources provide the ability to export output to several formats:

 * XML
 * JSON
 * CSV
 * XLSX (you must install library XlsxWriter)
 * PDF (you must install library reportlab)

List view provides export buttons. Option ``export_types`` contains tripple:
 * title
 * type
 * serialization format (content-type).

 For example if you want to serialize users to CSV::

    class UIRESTUserISCore(UIRESTISCore):
        export_types = (
            ('export to csv', 'csv', 'text/csv'),
        )

If you want to set ``export_types`` for all cores you can use ``EXPORT_TYPES`` attribute in your settings::

    EXPORT_TYPES = (
        ('export to csv', 'csv', 'text/csv'),
    )

.. attribute:: UIModelISCore.default_list_filter

UI table view support filtering data from REST resource. There are situations where you need to set default values for
filters. For example if you want to filter only superusers you can use::

    class UIRESTUserISCore(UIRESTISCore):
        default_list_filter = {
            'filter': {
                'is_superuser': True
            }
        }

On the other hand if you want to filter all users that is not superusers::

    class UIRESTUserISCore(UIRESTISCore):
        default_list_filter = {
            'exclude': {
                'is_superuser': True
            }
        }

Exclude and filter can be freely combined::

    class UIRESTUserISCore(UIRESTISCore):
        default_list_filter = {
            'filter': {
                'is_superuser': True
            },
            'exclude': {
                'email__isnull': True
            }
        }

.. attribute:: UIModelISCore.form_inline_views

The **django-is-core** interface has the ability to edit models on the same page as a parent model. These are called 
inlines. We will use as example new model issue of issue tracker system::


    class Issue(models.Model):
        name = models.CharField(max_length=100)
        watched_by = models.ManyToManyField(AUTH_USER_MODEL)
        created_by = models.ForeignKey(AUTH_USER_MODEL)

Now we want to add inline form view of all reported issues to user **add** and **edit** views::

    class ReportedIssuesInlineView(TabularInlineFormView):
        model = Issue
        fk_name = 'created_by'

    class UIRESTUserISCore(UIRESTISCore):
        form_inline_views = (ReportedIssuesInlineView,)

The ``fk_name`` is not required if there is only one relation between ``User`` and ``Issue``. More about inline views you
can find in generic views section # TODO add link.

.. attribute:: UIModelISCore.form_fieldsets

Set ``form_fieldsets`` to control the layout of core **add** and **change** pages. Fieldset defines a list of form fields
too. If you set ``form_fieldsets`` the ``form_fields`` is rewritten with a set of all fields from fieldsets.
Therefore you should use only one of these attributes.

``form_fieldsets`` is a list of two-tuples, in which each two-tuple represents a <fieldset> on the core form page. 
(a <fieldset> is a **section** of the form.).

The two-tuples are in the format (``name``, ``field_options``), where name is a string representing the title of the 
``form_fieldset`` and ``field_options`` is a dictionary of information about the ``fieldset``, including a list of fields 
to be displayed in it.

As a example we will use ``User`` model again::

    class UIRESTUserISCore(UIRESTISCore):
        form_fieldsets = (
            (None, {'fields': ('username', 'email')}),
            ('profile', {'fields': ('first_name', 'last_name'), 'classes': ('profile',)}),
        )

If neither ``form_fieldsets`` nor ``form_fields`` options are present, **Django** will default to displaying each field
that isn’t an ``AutoField`` and has ``editable=True``, in a single ``fieldset``, in the same order as the fields are
defined in the model.

The ``field_options`` dictionary can have the following keys:

 * fields

  A tuple of field names to display in this ``fieldset``. This key is required.

  Example::

    {
        'fields': ('first_name', 'last_name'),
    }

  fields can contain values defined in ``form_readonly_fields`` to be displayed as read-only.

  If you add ``callable`` to fields its result will be displayed as read-only.

 * classes

  A list or a tuple containing extra CSS classes to apply to the fieldset.

  Example::

    {
        'classes': ('profile',),
    }

 * inline_view

  ``inline_view`` attribute can not be defined together with ``fields``. This attribute is used for definig position of
  inline view inside form view. The value of the attribute is a string class name of the inline view.

  Example::

     {
         'inline_view': 'ReportedIssuesInlineView'
     }

.. attribute:: UIModelISCore.form_readonly_fields

By default the **django-is-core** shows all fields as editable. Any fields in this option (which should be a list or
a tuple) will display its data as-is and non-editable. Compare to **django-admin** fields defined in a form are used
too (due ``SmartModelForm``).

.. attribute:: UIModelISCore.menu_url_name

``menu_url_name`` is set to ``list`` by default, for all ``UIModelISCore`` and its descendants.

Methods
^^^^^^^

.. method:: UIISCore.get_form_fieldsets(request, obj=None)

Use this method if you want to change ``form_fieldsets`` dynamically.

.. method:: UIISCore.get_form_readonly_fields(request, obj=None)

Use this method if you want to change ``form_readonly_fields`` dynamically.

.. method:: UIISCore.get_ui_form_class(request, obj=None)

Change this method to get a custom form only for UI. By default it uses ``get_ui_form_class(request, obj)`` method
to obtain a form class.

.. method:: UIISCore.get_ui_form_fields(request, obj=None)

Change this method to get a custom form fields only for UI. By default it uses ``get_form_fields(request, obj)`` method
to obtain form fields.

.. method:: UIISCore.get_ui_form_exclude(request, obj=None)

Change this method to get a custom form exclude fields only for UI. By default it uses
``get_form_exclude(request, obj)`` method to obtain excluded form fields.

.. method:: UIISCore.get_form_inline_views(request, obj=None)

Use this method if you want to change ``form_inline_views`` dynamically.

.. method:: UIISCore.get_default_list_filter(request)

Use this method if you want to change ``default_list_filter`` dynamically.

.. method:: UIISCore.get_list_display(request)

Use this method if you want to change ``list_display`` dynamically.

.. method:: UIISCore.get_export_display(request)

Method returns ``export_display`` if no export_display is set the output is result of method
``get_list_display(request)``.

.. method:: UIISCore.get_export_types(request)

Use this method if you want to change ``export_types`` dynamically.

.. method:: UIISCore.get_api_url_name(request)

Use this method if you want to change ``api_url_name`` dynamically.

.. method:: UIISCore.get_api_url(request)

A result of this method is an URL string of REST API. The URL is generated with **Django** reverse function from
``api_url_name`` option.

.. method:: UIISCore.get_add_url(request)

Returns an URL string of **add** view. Rewrite this method if you want to change a link of add button at the list view.

RESTModelISCore
---------------

``RESTModelISCore`` represents core that provides a standard resource with default CRUD operations.

Options
^^^^^^^

.. attribute:: RESTModelISCore.rest_detailed_fields

Set ``rest_detailed_fields`` if you want to define fields that will be returned inside REST response for a request on
concrete object (an URL contains an ID of a concrete model object. For example an URL of a request is ``/api/user/1/``).
This option rewrites settings inside ``RESTMeta`` (you can find more about it at section #TODO add link).

.. attribute:: RESTModelISCore.rest_general_fields

Set ``rest_general_fields`` if you want to define fields that will be returned inside REST response for a request on
more than one object (an URL does not contain an ID of a concrete objects, eq. ``/api/user/``). This defined set of
fields is used for generating result of a foreign key object. This option rewrites settings inside ``RESTMeta``
(you can find more about it at section #TODO add link).

.. attribute:: RESTModelISCore.rest_extra_fields

Use ``rest_extra_fields`` to define extra fields that is not returned by default, but can be extra requested
by a HTTP header ``X-Fields`` or a GET parameter ``_fields``. More info you can find in **django-piston** library
documentation. This option rewrites settings inside ``RESTMeta`` (you can find more about it at section #TODO add link).

.. attribute:: RESTModelISCore.rest_default_guest_fields

``rest_guest_fields`` contains list of fields that can be seen by user that has not permission to see the whole
object data. In case that a user has permission to see an object that is related with other object that can not be
seen. In this situation is returned only fields defined inside ``rest_guest_fields``. This option rewrites settings
inside ``RESTMeta`` (you can find more about it at section #TODO add link).

.. attribute:: RESTModelISCore.rest_default_detailed_fields

The purpose of ``rest_default_detailed_fields`` is the same as ``rest_detailed_fields`` but this option does not rewrite
settings inside ``RESTMeta`` but the result fields is intersection of ``RESTMeta`` options and this option.

.. attribute:: RESTModelISCore.rest_default_general_fields

The purpose of ``rest_default_general_fields`` is the same as ``rest_general_fields`` but this option does not rewrite
settings inside ``RESTMeta`` but the result fields is intersection of ``RESTMeta`` options and this option.

.. attribute:: RESTModelISCore.rest_default_extra_fields

The purpose of ``rest_default_extra_fields`` is the same as ``rest_extra_fields`` but this option does not rewrite
settings inside ``RESTMeta`` but the result fields is intersection of ``RESTMeta`` options and this option.

.. attribute:: RESTModelISCore.rest_default_guest_fields

The purpose of ``rest_default_guest_fields`` is the same as ``rest_guest_fields`` but this option does not rewrite
settings inside ``RESTMeta`` but the result fields is intersection of ``RESTMeta`` options and this option.

.. attribute:: RESTModelISCore.rest_allowed_methods

A default value of ``rest_allowed_methods`` is::

    rest_allowed_methods = ('get', 'delete', 'post', 'put')

Use this option to remove a REST operation from a model REST resource. For example if you remove ``post``, the REST
resource will not be able to create new model object::

    rest_allowed_methods = ('get', 'delete', 'put')

.. attribute:: RESTModelISCore.rest_obj_class_names

This option is used with ``UIIScore``. A REST resource will return a list of defined class names inside a response.
The atribute inside response has named ``_class_names``.

.. attribute:: RESTModelISCore.rest_resource_class

A default resource class is ``RESTModelResource``. You can change it with this attribute.