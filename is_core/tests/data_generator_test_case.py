

class DataGeneratorTestCase(object):

    factories = {}

    @classmethod
    def get_model_label(cls, model):
        return '%s.%s' % (model._meta.app_label, model._meta.object_name)

    def new_instance(self, model, only_build=False):
        model_label = self.get_model_label(model)
        if self.factories.has_key(model_label):
            if only_build:
                return self.factories.get(model_label).build()
            else:
                return self.factories.get(model_label)()
