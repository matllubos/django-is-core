
Views
=====

Add view
---------

The generic view in ``is_core.generic_views.add_views`` is used to generate the add UI web page from django model classes.

The view named ``DjangoAddFormView`` is always related to core. The configuration (like fields, permissions, etc.) of the view can be defined here or in the core.

DjangoAddFormView

Detail view
-----------

DjangoDetailFormView
DjangoReadonlyDetailView
DjangoRelatedCoreTableView


List/Table view
---------------

DjangoTableView

Form view
---------

BulkChangeFormView
DjangoCoreFormView
DjangoBaseFormView

Inlines
-------

Inline generic views
^^^^^^^^^^^^^^^^^^^^

TabularGenericInlineFormView
StackedGenericInlineFormView
ResponsiveGenericInlineFormView

Inline form views
^^^^^^^^^^^^^^^^^

TabularInlineFormView
StackedInlineFormView
ResponsiveInlineFormView

Inline object views
^^^^^^^^^^^^^^^^^^^

TabularInlineObjectsView
ResponsiveInlineObjectsView

Inline table views
^^^^^^^^^^^^^^^^^^

DjangoInlineTableView