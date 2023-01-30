.. django-is-core documentation master file, created by
   sphinx-quickstart on Wed Aug 26 20:27:52 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==============================
Django-is-core's documentation
==============================

Django-is-core is application/framework for simple development of a Information System. You will find that it is very simlar to django admin but there si several differences that justifies why we created own implementation.

Features
========

- Django-is-core has same detail/add/table views as admin, but it uses REST and AJAX call to achieve it. It adds easier usage and broaden usability.
- Django-is-core can be used for creation only REST resources without UI.
- Models UI (add/detail) is more linked together. Links between foreign keys are automatically added.
- Django-is-core provides more posibilities for readonly fields. For example the fields defined only inside form can be readonly too.
- Exports to xlsx, pdf, csv can be very simply add to table view.
- Better permissions, for example link between objects is not added to UI if user does not have permission to see the object.
- Add new custom view is for django admin nightmare. With django-is-core it is very easy.
- Django-is-core views as implemented with using generic views not as method. It is cleaner and changes are simplier.
- Add new model administration without its registration.
- Better objects filters from UI (automatically respond to user typing) and coding (easier new filter implementation) perspective too.
- Token authorization.
- And much much more.

Project Home
------------
https://github.com/matllubos/django-is-core

Documentation
-------------
https://django-is-core.readthedocs.org/en/latest

Content
=======

.. toctree::
   :maxdepth: 2

   installation
   cores
   views
   rests
   permissions
   forms
   filters
   utils
   menu
   elasticsearch
   dynamodb
