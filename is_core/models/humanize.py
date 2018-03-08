from django.utils.html import format_html


def url_humanized(field, val, *args, **kwargs):
    return format_html('<a href="{0}">{0}</a>', val) if val else val