from is_core.tests.factory.fields import delete_test_files


class DataGeneratorTestCase:

    factories = {}

    @classmethod
    def tearDownClass(cls):
        super(DataGeneratorTestCase, cls).tearDownClass()
        delete_test_files()

    @classmethod
    def get_model_label(cls, model):
        return '%s.%s' % (model._meta.app_label, model._meta.object_name)

    def new_instance(self, model, only_build=False):
        model_label = self.get_model_label(model)
        if model_label in self.factories:
            if only_build:
                return self.factories.get(model_label).build()
            else:
                return self.factories.get(model_label)()
