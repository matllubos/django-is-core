from django.forms import DecimalField as OriginDecimalField


class DecimalField(OriginDecimalField):

    def __init__(self, *args, **kwargs):
        self.step = kwargs.pop('step', 'any')
        super(DecimalField, self).__init__(*args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super(DecimalField, self).widget_attrs(widget)
        attrs['step'] = self.step
        return attrs

