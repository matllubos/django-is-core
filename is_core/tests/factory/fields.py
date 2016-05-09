import os
import factory


class TemporaryFileField(factory.django.FileField):
    temporary_files = []

    def call(self, obj, create, extraction_context):
        field_file = super(TemporaryFileField, self).call(obj, create, extraction_context)
        self.temporary_files.append(field_file)
        return field_file

    @classmethod
    def delete_test_files(cls):
        for temporary_file in cls.temporary_files:
            os.remove(temporary_file.path)
        cls.temporary_files = []


class FileField(TemporaryFileField, factory.django.FileField):
    pass


class ImageField(TemporaryFileField, factory.django.ImageField):
    pass


def delete_test_files():
    TemporaryFileField.delete_test_files()
