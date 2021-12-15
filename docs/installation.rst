.. _installation:

Installation
============

Requirements
------------

Python/Django versions
^^^^^^^^^^^^^^^^^^^^^^

+------------------+------------+-----------+
| Modeltranslation | Python     | Django    |
+==================+============+===========+
| >=1.4            | 3.2 - 3.4  | 1.8 - 1.9 |
|                  +------------+-----------+
|                  | 2.7        | 1.8 - 1.9 |
+------------------+------------+-----------+
| <=1.3            | 2.7        | 1.6 - 1.8 |
+------------------+------------+-----------+


Libraries
^^^^^^^^^

 * **django-class-based-auth-views** - Login/Logout views as generic view structure
 * **django-piston** - not original pistion library, but improved. You can find it here https://github.com/matllubos/django-piston
 * **django-block-snippets** - library providing block snippets of html code for easier development webpages with ajax. You can find it here https://github.com/matllubos/django-block-snippets
 * **django-chamber** - several helpers removing code duplication. You can find it here https://github.com/matllubos/django-chamber
 * **python-dateutil** - provides powerful extensions to the datetime module available in the Python standard library
 * **django-apptemplates** - Django template loader that allows you to load a template from a specific application
 * **django-project-info** - small library getting project version to django context data
 * **pillow** - Python imaging library (optional)
 * **germanium** - framework for testing purposes (optional)
 * **factory-boy** - testing helper for creating model data for tests (optional)

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

After instalation you must go throught these steps to use django-is-core:

Required Settings
-----------------

The following variables have to be added to or edited in the project's ``settings.py``:

``INSTALLED_APPS``
^^^^^^^^^^^^^^^^^^

For using is-core you just add add ``is_core`` and ``block_snippets`` to ``INSTALLED_APPS`` variable::

    INSTALLED_APPS = (
        ...
        'is_core',
        'block_snippets',
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
2. Sync database with command ``python manage.py syncdb`` or ``python manage.py migrate``

Advanced Settings
=================

Token authentification
----------------------

Because django-is-core provides simple way how to create Information Systems based on REST the standard django session authentification is not ideal for this purpose.

Django-is-core provides token authentification. The advantages of this method are:
1. You can use fat client that can not use cookies.
2. Every token conains information about connected device. So you can watch user activity.
3. You can lead connected users by expiration time or deactivate user token to logout authentificated user.

If you want to use token authentification follow these steps:

``INSTALLED_APPS``
^^^^^^^^^^^^^^^^^^

Add ``is_core.auth_token`` right after ``is_core`` inside ``INSTALLED_APPS`` variable::

    INSTALLED_APPS = (
        ...
        'is_core',
        'is_core.auth_token',
        'block_snippets',
        ...
    )

``MIDDLEWARE_CLASSES``
^^^^^^^^^^^^^^^^^^^^^^

Replace ``django.contrib.auth.middleware.AuthenticationMiddleware`` with ``is_core.auth_token.middleware.TokenAuthenticationMiddlewares`` inside ``MIDDLEWARE_CLASSES``

``Setup``
^^^^^^^^^

Finally again sync database models, because auth_token adds new django models (``python manage.py syncdb`` or ``python manage.py migrate``)
