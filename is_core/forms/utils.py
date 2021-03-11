from django.utils.html import format_html


def add_class_name(attrs, class_name):
    class_names = attrs.get('class')
    if class_names:
        class_names = [class_names]
    else:
        class_names = []
    class_names.append(class_name)
    attrs['class'] = ' '.join(class_names)
    return attrs


class ReadonlyValue:

    def __init__(self, value, humanized_value):
        self._value = value
        self._humanized_value = humanized_value

    def render(self):
        if self._humanized_value is None:
            return format_html(
                '<p>{}</p>',
                self._value,
            )
        else:
            return format_html(
                '<p><span title="{}">{}</span></p>',
                self._value,
                self.value
            )

    @property
    def value(self):
        return self._humanized_value if self._humanized_value is not None else self._value