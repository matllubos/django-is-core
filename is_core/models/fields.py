from django.contrib.contenttypes.fields import GenericForeignKey as OriginGenericForeignKey


class GenericForeignKey(OriginGenericForeignKey):

    def __init__(self, *args, **kwargs):
        self.verbose_name = kwargs.pop('verbose_name', None)
        super().__init__(*args, **kwargs)
