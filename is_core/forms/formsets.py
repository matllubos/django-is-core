from django.forms.formsets import DEFAULT_MAX_NUM, BaseFormSet as OriginBaseFormSet


class BaseFormSetMixin:
    """
    Mixin that add method all_forms which return existing forms and empty form in one list
    """

    def __init__(self, *args, **kwargs):
        super(BaseFormSetMixin, self).__init__(*args, **kwargs)
        self._all_forms = None

    def all_forms(self):
        if self._all_forms is None:
            self._all_forms = []
            for form in self.forms:
                self._all_forms.append(form)

            if self.can_add:
                self._all_forms.append(self.empty_form)
        return self._all_forms

    def total_form_count(self):
        total_form_count = super(BaseFormSetMixin, self).total_form_count()
        if total_form_count < self.min_num:
            return self.min_num
        return total_form_count


class BaseFormSet(BaseFormSetMixin, OriginBaseFormSet):
    pass


def smartformset_factory(form, formset=BaseFormSet, extra=1, can_order=False,
                         can_delete=False, min_num=None, max_num=None, validate_min=False, validate_max=False):
    """Return a FormSet for the given form class."""
    if max_num is None:
        max_num = DEFAULT_MAX_NUM
    # hard limit on forms instantiated, to prevent memory-exhaustion attacks
    # limit is simply max_num + DEFAULT_MAX_NUM (which is 2*DEFAULT_MAX_NUM
    # if max_num is None in the first place)
    absolute_max = max_num + DEFAULT_MAX_NUM
    if min_num is None:
        min_num = 0

    attrs = {'form': form, 'extra': extra,
             'can_order': can_order, 'can_delete': can_delete, 'min_num': min_num,
             'max_num': max_num, 'absolute_max': absolute_max, 'validate_min': validate_min,
             'validate_max': validate_max}
    return type(form.__name__ + str('FormSet'), (formset,), attrs)
