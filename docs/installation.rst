.. _installation:

Installation
============

Requirements
------------

Python/Django versions
^^^^^^^^^^^^^^^^^^^^^^

+----------------------------+------------------+
|  Python                    | Django           |
+============================+==================+
| 3.5, 3.6, 3.9, 3.10, 3.11  | >=2.2 <4         |
+----------------------------+------------------+


Libraries
^^^^^^^^^

 * **django-class-based-auth-views** - Login/Logout views as generic view structure
 * **django-pyston** - not original pistion library, but improved. You can find it here https://github.com/druids/django-pyston
 * **django-block-snippets** - library providing block snippets of html code for easier development webpages with ajax. You can find it here https://github.com/druids/django-block-snippets
 * **django-chamber** - several helpers removing code duplication. You can find it here https://github.com/druids/django-chamber

All optional libraries is not instaled automatically. Other libraries are dependecies of django-is-core.

Using Pip
---------

Django is core is not currently inside *PyPE* but in the future you will be able to use:

.. code-block:: console

    $ pip install django-is-core


Because *django-is-core* is rapidly evolving framework the best way how to install it is use source from github

.. code-block:: console

    $ pip install https://github.com/matllubos/django-is-core/tarball/{{ version }}#egg=django-is-core-{{ version }}

Configuration
=============

After installation you must go through these steps to use django-is-core:

Required Settings
-----------------

The following variables have to be added to or edited in the project's ``settings.py``:

``INSTALLED_APPS``
^^^^^^^^^^^^^^^^^^

For using is-core you just add add ``is_core``, ``pyston`` and ``block_snippets`` to ``INSTALLED_APPS`` variable::

    INSTALLED_APPS = (
        ...
        'is_core',
        'block_snippets',
        'pyston',
        ...
    )

``MIDDLEWARE_CLASSES``
^^^^^^^^^^^^^^^^^^^^^^

Next add two middlewares to end of ``MIDDLEWARE_CLASSES`` variable::

    MIDDLEWARE_CLASSES = (
        ...
        'is_core.middleware.RequestKwargsMiddleware',
        'is_core.middleware.HttpExceptionsMiddleware',
    )

Setup
=====
To finally setup the application please follow these steps:

1. Collect static files from django-is-core with command ``python manage.py collectstatic``
2. Sync database with command ``python manage.py migrate``


Settings
========

These configuration you can use with django-is-core in your django settings file:

.. attribute:: IS_CORE_AUTH_LOGIN_VIEW

  Path to the login view class. If library ``django-auth-token`` is installed its view are used otherwise ``is_core.views.auth.LoginView`` is selected as the view.

.. attribute:: IS_CORE_AUTH_LOGIN_CODE_VERIFICATION_VIEW

  Administration supports two factor login. If it is turned on and ``django-auth-token`` is installed the view from this library is used. Otherwise none is set.

.. attribute:: IS_CORE_AUTH_FORM_CLASS

  Django form class for the login view.

.. attribute:: IS_CORE_AUTH_RESOURCE_CLASS

  If you want to allow login view on the is-core REST you can implement and set the pyston resource login class. The REST login is turned off by default and the setting is set to ``None``.

.. attribute:: IS_CORE_AUTH_LOGOUT_VIEW

  Path to the logout view. If library ``django-auth-token`` is installed its view are used otherwise ``'is_core.views.auth.LogoutView'`` is set by default.

.. attribute:: IS_CORE_CODE_VERIFICATION_URL

  The URL path to the second factor. The default value is ``'/login/login-code-verification/'``.

.. attribute:: IS_CORE_HOME_CORE

  The core class for the administration home page. The default value is ``'is_core.main.HomeUiCore'``.

.. attribute:: IS_CORE_HOME_VIEW

  The view class for the administration home page. The default value is ``'is_core.generic_views.base.HomeView'``.

.. attribute:: IS_CORE_MENU_GENERATOR

  The path to the is-core menu generator. The default value is ``'is_core.menu.MenuGenerator'``.

.. attribute:: IS_CORE_USERNAME

  The admin user username field name. The default value is ``'username'``.

.. attribute:: IS_CORE_PASSWORD

  The admin user password field name. The default value is ``'password'``.

.. attribute:: IS_CORE_LOGIN_URL

  The login URL path. The default value is ``'/login/'``.

.. attribute:: IS_CORE_LOGOUT_URL

  The logout URL path. The default value is ``'/logout/'``.

.. attribute:: IS_CORE_LOGIN_API_URL

  The API login URL path. The default value is ``'/api/login/'``.

.. attribute:: IS_CORE_EXPORT_TYPES

  The list of the export types for the administration. The default value is ``None``::

    IS_CORE_EXPORT_TYPES = (
        ('XLSX', 'xlsx', 'VERBOSE'),
        ('CSV', 'csv', 'VERBOSE'),
        ('TXT', 'txt', 'VERBOSE'),
    )

.. attribute:: IS_CORE_FOREIGN_KEY_MAX_SELECTBOX_ENTRIES

  Max entries int the foreign key select boxes. If there is more foreign key boxes the select box is replaced with HTML input. The default value is ``500``

.. attribute:: IS_CORE_LIST_PER_PAGE

  The default number of elements returned in the table. The default value is ``20``.

.. attribute:: IS_CORE_REST_PAGINATOR_MAX_TOTAL

  The maximum elements which can be returned in one REST response. The default value is ``10000``.

.. attribute:: IS_CORE_RESPONSE_EXCEPTION_FACTORY

  The response generator if an expected exception is raised. The default value is ``'is_core.exceptions.response.ui_rest_response_exception_factory'``.

.. attribute:: IS_CORE_DEFAULT_FIELDSET_TEMPLATE

  The path to the form fieldset template. The default value is ``'is_core/forms/default_fieldset.html'``.

.. attribute:: IS_CORE_HEADER_IMAGE

  The path to the header image of the administration.

.. attribute:: IS_CORE_ENVIRONMENT

  The environment name which is printed in the administration.

.. attribute:: IS_CORE_BACKGROUND_EXPORT_TASK_TIME_LIMIT

  The maximal time of the export task. The default value is 1h.

.. attribute:: IS_CORE_BACKGROUND_EXPORT_TASK_SOFT_TIME_LIMIT

  The maximal soft time of the export task. The default value is 1h minus 5 minutes.

.. attribute:: IS_CORE_BACKGROUND_EXPORT_TASK_UPDATE_REQUEST_FUNCTION

  The path to the function which can be used to update request for the file export::

    # Django settings
    IS_CORE_BACKGROUND_EXPORT_TASK_UPDATE_REQUEST_FUNCTION = 'your.file.update_background_export_request'

    # your/file.py
    def update_background_export_request(request):
        request.user = request.user.subclass
        return request

.. attribute:: IS_CORE_BACKGROUND_EXPORT_TASK_QUEUE

  The celery queue name which will be used for the background export.

.. attribute:: IS_CORE_BACKGROUND_EXPORT_SERIALIZATION_LIMIT

  The maximal elements serialized in the background export. The default value is ``2000``.

.. attribute:: IS_CORE_BACKGROUND_EXPORT_STORAGE_CLASS

  The background export storage class where the file will be stored. The default value is ``'django.core.files.storage.DefaultStorage'``.

.. attribute:: IS_CORE_BACKGROUND_EXPORT_EXPIRATION_DAYS

  The background export expiration days for the exported files. The default value is 30 days.

.. attribute:: IS_CORE_COLUMN_MANAGER

  Allow administration column manager (table columns can be hidden with this function). The defalut value is ``False``.



