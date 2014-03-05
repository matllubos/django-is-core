from django.core.urlresolvers import reverse
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django import forms

from is_core.utils import query_string_from_dict
from django.forms.util import flatatt


class WrapperWidget(forms.Widget):

    def __init__(self, widget):
        self.widget = widget

    @property
    def media(self):
        return self.widget.media

    @property
    def attrs(self):
        return self.widget.attrs

    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        self.attrs = self.widget.build_attrs(extra_attrs=None, **kwargs)
        return self.attrs

    def value_from_datadict(self, data, files, name):
        return self.widget.value_from_datadict(data, files, name)

    def _has_changed(self, initial, data):
        return self.widget._has_changed(initial, data)

    def id_for_label(self, id_):
        return self.widget.id_for_label(id_)


# TODO: It may seem unnecessarily complicated, but will use it elsewhere
class RelatedFieldWidgetWrapper(WrapperWidget):

    def __init__(self, widget, model, site_name):
        super(RelatedFieldWidgetWrapper, self).__init__(widget)
        self.model = model
        self.site_name = site_name
        self.choices = self.widget.choices

    def render(self, name, value, attrs):
        from is_core.site import get_model_view

        model_view = get_model_view(self.model)
        if model_view:

            info = model_view.site_name, model_view.get_menu_group_pattern_name()
            attrs['data-resource'] = reverse('%s:api-%s' % info)
            attrs['data-fields'] = ','.join(self.model._rest_meta.selectbox_fields)
            if self.model._rest_meta.image_field:
                attrs['data-image-field'] = self.model._rest_meta.image_field


            if hasattr(self.widget, 'limit_choices_to'):
                attrs['data-resource'] = '%s?%s' % (attrs['data-resource'],
                                                    query_string_from_dict(self.widget.limit_choices_to))

        output = (
            self.widget.render(name, value, attrs),
        )

        return mark_safe(''.join(output))


# TODO: Revrite this code
class Html(object):

    def __init__(self, tag, attrs=None, text_or_pair=False):
        self.tag = tag
        self.attrs = attrs or {}
        self.text_or_pair = text_or_pair
        self.children = None

    def add(self, el):
        if self.children is None:
            self.children = []
        self.children.append(el)

    def __str__(self):
        tokens = ['<', self.tag, flatatt(self.attrs), '>']

        if self.children:
            for child in self.children:
                tokens.append(child.__str__())

        if self.text_or_pair:
            text = ''
            if not isinstance(self.text_or_pair, bool):
                text = force_text(self.text_or_pair)
            tokens.extend((text, '</', self.tag, '>'))
        return ''.join(tokens)

    @staticmethod
    def el(tag, attrs=None, text_or_pair=False):
        return Html(tag, attrs, text_or_pair).__str__()

    @staticmethod
    def btn(attrs, text):
        title = text
        if 'title' in attrs:
            title = attrs['title']
        attrs['type'] = 'button'
        attrs['title'] = title
        span = Html('span', None, text)
        btn = Html('button', attrs, True)
        btn.add(span)
        return btn.__str__()
