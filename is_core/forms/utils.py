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
        self.value = value
        self.humanized_value = humanized_value
