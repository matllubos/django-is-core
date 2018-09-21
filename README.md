Prolog
======

Django IS Core is a lightweight framework built on Django. It augments Django great design patterns and minimizes
annoying programming work. It takes best from Django-admin. ISCore provides a simple way how to build a rich
administration. It is very simlar to Django admin but there are several differences that justifies why IS Core is
created.

Features
--------

* same detail/add/table views as Django admin, but it uses REST and AJAX call to achieve it (it adds easier usage and
broaden usability)
* it can be used for creation only REST resources without UI
* models UI (add/detail) is more linked together, links between foreign keys are automatically added
* it provides more posibilities for read-only fields (e.g. the fields defined only inside form can be readonly too)
* add new custom view is for Django admin is nightmare, with IS Core is very easy
* it uses class based views, it is cleaner and changes are simplier
* add new model administration without its registration
* generated forms from models with validations
* generated REST resources from models again with validations (no code duplication)
* automatic exports to XLSX, PDF, CSV can be very simply add to a table view
* automatic filtering and sorting for list views
* pre-built reusable views and forms
* automatic CRUD views for models (with REST resources)
* authorization (token based) and permissions
* advanced permissions (e.g. a link between objects is not added to UI if a user does not have permissions to see it)
* and much more ...

Docs
----

For more details see [docs](http://django-is-core.readthedocs.org/)


Contribution
------------

To run Livereload for Sphinx you need [livereload](https://pypi.python.org/pypi/livereload) `pip install livereload`.
After installing simply call `make htmllivereload` and open [http://localhost:5500/](http://localhost:5500/).