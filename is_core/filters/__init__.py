class UIFilterMixin(object):

    widget = None

    def get_widget(self, request):
        widget = self.widget
        if isinstance(widget, type):
            widget = widget()
        return widget
