from __future__ import unicode_literals


def add_class_name(attrs, class_name):
    class_names = attrs.get('class')
    if class_names:
        class_names = [class_names]
    else:
        class_names = []
    class_names.append(class_name)
    attrs['class'] = ' '.join(class_names)
    return attrs
