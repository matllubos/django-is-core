from is_core.main import ModelCore, ModelUiCore, ModelUiRestCore, ModelRestCore

from .filters import CoreElasticsearchFilterManagerFilterManager
from .paginator import ElasticsearchOffsetBasedPaginator
from .resources import ElasticsearchCoreResource
from .views import ElasticsearchDetailView, ElasticsearchTableView


class ElasticsearchCore(ModelCore):

    abstract = True

    @property
    def menu_group(self):
        return self.model._index._name.replace('-', '_')

    def get_queryset(self, request):
        queryset = self.model.search()
        ordering = self.get_default_ordering()
        if ordering:
            queryset = queryset.sort(*ordering)
        return queryset


class ElasticsearchUiCore(ElasticsearchCore, ModelUiCore):

    abstract = True

    ui_list_view = ElasticsearchTableView
    ui_detail_view = ElasticsearchDetailView


class ElasticsearchRestCore(ElasticsearchCore, ModelRestCore):

    abstract = True

    rest_resource_class = ElasticsearchCoreResource
    rest_paginator = ElasticsearchOffsetBasedPaginator()
    rest_filter_manager = CoreElasticsearchFilterManagerFilterManager()


class ElasticsearchUiRestCore(ElasticsearchRestCore, ElasticsearchUiCore, ModelUiRestCore):

    abstract = True
