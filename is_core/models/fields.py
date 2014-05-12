from django.db.models import FileField as OriginFileField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text

from is_core import config

try:
    from sorl.thumbnail import ImageField as OriginImageField
except ImportError:
    from django.db.models import ImageField as OriginImageField


class RestrictedFileFieldMixin(object):
    """
    Same as FileField, but you can specify:
        * content_types - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
        * max_upload_size - a number indicating the maximum file size allowed for upload in MB.
    """
    def __init__(self, *args, **kwargs):
        self.max_upload_size = kwargs.pop("max_upload_size", config.MAX_UPLOAD_SIZE) * 1024 * 1024

        super(RestrictedFileFieldMixin, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(RestrictedFileFieldMixin, self).clean(*args, **kwargs)

        if data.file.size > self.max_upload_size:
            raise forms.ValidationError(_('Please keep filesize under %(max)s. Current filesize %(current)s') %
                                        {
                                         'max': filesizeformat(self.max_upload_size),
                                         'current': filesizeformat(data.file.size)
                                         })
        return data

    def south_field_triple(self):
        from south.modelsinspector import introspector
        cls_name = '%s.%s' % (self.__class__.__module__ , self.__class__.__name__)
        args, kwargs = introspector(self)
        return (cls_name, args, kwargs)

    def get_filename(self, filename):
        """
        removes UTF chars from filename
        """
        from unidecode import unidecode
        return super(RestrictedFileFieldMixin, self).get_filename(unidecode(force_text(filename)))


class FileField(RestrictedFileFieldMixin, OriginFileField):
    pass


class ImageField(RestrictedFileFieldMixin, OriginImageField):
    pass
