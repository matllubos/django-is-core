import django.dispatch


export_success = django.dispatch.Signal(providing_args=['exported_file'])
