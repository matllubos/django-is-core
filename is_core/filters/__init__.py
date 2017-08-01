class UIFilterMixin(object):

    widget = None

    def get_widget(self, request):
        return self.widget