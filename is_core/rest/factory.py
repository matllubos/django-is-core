from is_core.rest.resource import RestModelResource


def modelrest_factory(model, resource_class=RestModelResource, register=True):
    resource_kwargs = {
        'model': model,
        'register': register
    }
    class_name = model.__name__ + str('Resource')
    return type(resource_class)(class_name, (resource_class,), resource_kwargs)
