from django.forms.formsets import DEFAULT_MAX_NUM, BaseFormSet as OriginBaseFormSet
from django.utils.functional import cached_property


class BaseFormSetMixin(object):
    """
    Mixin that add method all_forms which return existing forms and empty form in one list
    """

    @cached_property
    def all_forms(self):
        self._all_forms = []
        for form in self.forms:
            self._all_forms.append(form)

        if self.can_add:
            self._all_forms.append(self.empty_form)
        return self._all_forms


class BaseFormSet(BaseFormSetMixin, OriginBaseFormSet):
    pass


def smartformset_factory(form, formset=BaseFormSet, extra=1, can_order=False,
                    can_delete=False, min_num=None, max_num=None, validate_min=False, validate_max=False):
    """Return a FormSet for the given form class."""
    if min_num is None:
        min_num = DEFAULT_MIN_NUM
    if max_num is None:
        max_num = DEFAULT_MAX_NUM
    # hard limit on forms instantiated, to prevent memory-exhaustion attacks
    # limit is simply max_num + DEFAULT_MAX_NUM (which is 2*DEFAULT_MAX_NUM
    # if max_num is None in the first place)
    absolute_max = max_num + DEFAULT_MAX_NUM
    attrs = {'form': form, 'extra': extra,
             'can_order': can_order, 'can_delete': can_delete,
             'min_num': min_num, 'max_num': max_num,
             'absolute_max': absolute_max, 'validate_min': validate_min,
             'validate_max': validate_max}
    return type(form.__name__ + str('FormSet'), (formset,), attrs)
