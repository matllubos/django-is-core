class BaseFormSetMixin(object):
    """
    Mixin that add method all_forms which return existing forms and empty form in one list
    """

    def all_forms(self):
        for form in self.forms:
            yield form

        if self.can_add:
            yield self.empty_form

    def total_form_count(self):
        total_form_count = super(BaseFormSetMixin, self).total_form_count()
        if total_form_count < self.min_num:
            return self.min_num
        return total_form_count
