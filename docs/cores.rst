
Cores
=====

UIRESTModelISCore
-----------------

The UIRESTModelISCore class is the representation of a model in the django-is-core interface. These representations are 
stored in a file named cores.py in your application. We will start with the most common cose when you want to create
three typical views for information system:

  * table view for printing objects
  * view for creating new objects
  * view for editing objects

As example project we use Issue tracker. Firstly for every application you need management of users. We use default 
django user model.

For creating add, edit and table views you must only create file cores.py inside specific application that contains::

    from django.contrib.auth.models import User

    from is_core.main import UIRESTModelISCore

    class UserIsCore(UIRESTModelISCore):
        model = User

There is no obligation for registration. Cores are registered automatically. The result views with previue are:

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
But there is created REST resource too. By default on URLs **/api/user/** and **/api/user/{obj_id}** that returns 
object in asked format (HTTP header **Content-type: application/json**).



RESTModelISCore
----------------

The RESTModelISCore is parent of UIRESTModelISCore. As the name suggests this class is used only for creating REST
resources without UI HTML views. The usage is the same as UIRESTModelISCore::

    from django.contrib.auth.models import User

    from is_core.main import RESTModelISCore

    class RESTUserIsCore(RESTModelISCore):
        model = User


UIModelISCore
-------------

The RESTModelISCore is the second parent of *UIRESTModelISCore*. It is used for creating only UI views. Because UI views 
needs some REST resources is necessary to specify on which URL is deployed REST resource of model (api_url_name is 
transofmed to URL by django resolve helper)::

    from django.contrib.auth.models import User

    from is_core.main import UIModelISCore

    class UIUserIsCore(UIModelISCore):
        model = User
        api_url_name = 'api-user'


You can specify URL manually::

    class UIUserIsCore(UIModelISCore):
        model = User

        def get_api_url(self, request):
            return '/api/user/'

ISCore hiearchy
---------------

Now we provide detailed description of all ISCore objects. Firstly for better understanding you can see UML class 
diagram of core hiearchy. 

# TODO add diagram


ISCore
------

Following options and methods can be applied for all Core objects like *RESTModelISCore*, *UIModelISCore* or 
*UIRESTModelISCore* (all descendants of ISCore class). 


Options
^^^^^^^

 .. attribute:: ISCore.abstract

Variable *abstract* provides way how to create core that is not registered but this class variable is not inherited. 
Let's show an example::

    from django.contrib.auth.models import User

    from is_core.main import RESTModelISCore

    class AbstractUIRESTUserIsCore(RESTModelISCore):
        model = User
        abstract = True
        verbose_name = 'example of abstract user core'

    class UIRESTUserIsCore(AbstractUIRESTUserIsCore):
        pass

First core is not registered. Therefore views and rest resources are not created. But the second view that inherits of 
abstract core is registered. All configuration from parent class is inhered (without abstract variable).

 .. attribute:: ISCore.verbose_name, ISCore.verbose_name_plural

These variables are used inside generic views. It can be added to context_data and rendered inside templates. 

 .. attribute:: ISCore.menu_group

It is necessary have some slug that distinguish one core from another. For this purpose is used variable menu_group.
This variable is used for example to generate URL patterns or menu. Value of the variable is generated automatically 
for cores that is connected to model 

Methods
^^^^^^^

 .. method:: ISCore.init_request(request)

Every core views/rest resources calls this method before calling dispatch. You can use it to change request its calling.

ModelISCore
-----------

Tne next class that extends ISCore is ModelISCore. All cores that inherits from ModelISCore works as controller over
a model.

Options
^^^^^^^

 .. attribute:: ModelISCore.list_actions

Variable *list_action* contains actions that user can perform via REST or UI. More detailed explanation with example
you find inside **UIRESTModelISCore options** part.

 .. attribute:: ModelISCore.form_fields

Use the form_fields option to make simple layout changes in the forms on the “add” and “edit” and REST resources pages 
such as showing only a subset of available fields, modifying their order, or grouping them into rows. We will show it
on UIRESTModelISCore. If you want to restrict form fields to *username*, *first_name* and *last_name* the simpliest
way is use:

    from django.contrib.auth.models import User

    from is_core.main import UIRESTModelISCore

    class UserIsCore(UIRESTModelISCore):
        model = User
        form_fields = ('username', 'fist_name', 'last_name')

 .. attribute:: ModelISCore.form_exclude

This attribute, if given, should be a list of field names to exclude from the form.

    from django.contrib.auth.models import User

    from is_core.main import UIRESTModelISCore

    class UserIsCore(UIRESTModelISCore):
        model = User
        form_exclude = ('password',)

 .. attribute:: ModelISCore.form_class

If you want to change default form class which is SmartModelForm you can change it with this option. The form is changed
for ^add^, ^edit^ views and REST resources too.

 .. attribute:: ModelISCore.ordering

Option for changing default ordering of model for core.

Methods
^^^^^^^

 .. method:: ModelISCore.get_form_fields(request, obj=None)

Use this method to define form fields dynamically or if you want to define different form fields for ^add^, ^edit^ view
of REST resources.


 .. method:: ModelISCore.get_form_exclude(request, obj=None)


The oposite to get_form_fields.

 .. method:: ModelISCore.get_form_class(request, obj=None)


Use this method to define form dynamically or if you want to define different form for ^add^, ^edit^ view of REST 
resources.

 .. method:: ModelISCore.pre_save_model(request, obj, form, change)

Method per_save_model is called before saving object to database. Body is empty by default.

 .. method:: ModelISCore.post_save_model(request, obj, form, change)

Method post_save_model is called after saving object to database. Body is empty by default.

 .. method:: ModelISCore.save_model(request, obj, form, change)

You can rewrite this method if you want to change way how is object saved to database. Default body is:

    def save_model(self, request, obj, form, change):
        obj.save()

 .. method:: ModelISCore.pre_delete_model(request, obj)

Method pre_delete_model is called before removing object from database. Body is empty by default.

 .. method:: ModelISCore.post_delete_model(request, obj)

Method post_delete_model is called after removing object from database. Body is empty by default.

 .. method:: ModelISCore.delete_model(request, obj)

You can rewrite this method if you want to change way how is object removed from database. Default body is:

    def delete_model(self, request, obj):
        obj.delete()

 .. method:: ModelISCore.verbose_name(), ModelISCore.verbose_name_plural()

Default verbose names of ModelISCore is get from model meta options:

    self.model._meta.verbose_name
    self.model._meta.verbose_name_plural

 .. method:: ModelISCore.menu_group()

Default menu_group value is get from module name of model (self.model._meta.module_name)

 .. method:: ModelISCore.get_ordering(request)

Use this method if you want to change ordering dynamically.

 .. method:: ModelISCore.get_queryset(request)

Returns model queryset, ordered by defined ordering inside core. You can filter here objects according to user 
permissions.

 .. method:: ModelISCore.preload_queryset(request, qs)

The related objects of queryset should sometimes very slow down retrieving data from the database. If you want to 
improve speed of your application use this function to create preloading of related objects.

 .. method:: ModelISCore.get_list_actions(request, obj)

Use this method if you want to change list_actions dynamically.


 .. method:: ModelISCore.get_default_action(request, obj)

Chose default action for object used inside UI and REST. For example default action is action that is performed if you
select row inside table of objects. For table view default action is ^open edit view^. If you return None no action
is performed by default.


UIISCore
--------

Options
^^^^^^^

 .. attribute:: UIISCore.menu_url_name

Every UI core has one place inside menu that addresses one of UI views of a core. This view is selected by option 
*menu_url_name*.

 .. attribute:: UIISCore.show_in_menu

Option *show_in_menu* is set to True by default. If you want to remove core view from menu set this option to False.

 .. attribute:: UIISCore.view_classes

Option contains view classes that are automatically added to django urls. Use this option to add new views. Example 
you can see in setion generic views. #TODO add link

 .. attribute:: UIISCore.default_ui_pattern_class

Every view must have assigned is-core pattern class. This pattern is not the same patter that is used with django
urls. This pattern has higher usability. You can use it to generate the url string or checking permissions. Option
default_ui_pattern_class contains pattern class that is used with defined view classes. More about patterns you can 
find in setcion patterns. #TODO add link

Methods
^^^^^^^

 .. method:: UIISCore.init_ui_request(request)

Every view defined with option view_classes calls this method before calling dispatch. The default implementation of
this method calls parent method *init_request*.

    def init_ui_request(self, request):
        self.init_request(request)

 .. method:: UIISCore.get_view_classes()

Use this method if you want to change view_classes dynamically.

 .. method:: UIISCore.get_ui_patterns()

Contains code that generates ui_patterns from view classes. Method returns ordered dict of pattern classes.


 .. method:: UIISCore.get_show_in_menu(request)

Returns boolean if menu link is provided for the core. By default there is three rules:

 * show_in_menu must be set to True.
 * menu_url_name need not be empty.
 * current user must have permission to see the linked view.


 .. method:: UIISCore.is_active_menu_item(request, active_group)

Method finds if menu link of a core is active (if the view with menu_url_name is the current displayed page).


 .. method:: UIISCore.get_menu_item(request, active_group)

Method returns menu item object that contains information about link that is displayed inside menu.

 .. method:: UIISCore.menu_url(request, active_group)

Return URL strin of menu item.






UIModelISCore
-------------

Options
^^^^^^^


 .. attribute:: UIModelISCore.form_inline_views

The django-is-core interface has the ability to edit models on the same page as a parent model. These are called 
inlines. The form_inline_views provides simple way 
