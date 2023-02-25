import os
from django import template
from django.utils.translation import gettext as _

register = template.Library()


@register.filter
def basename(value):
    return os.path.basename(value)


@register.filter
def no_permission_tags(permission_value):
    default_message = _('Funzionalità non attiva. Scopri i piani di InPublish!')
    if not permission_value:
        return f'data-toggle=tooltip data-placement=top title="{default_message}"'
    else:
        return ""


@register.filter
def no_permission_class(permission_value):
    if not permission_value:
        return "no-permission"
    else:
        return ""


@register.filter
def no_permission_name(permission_value, name):
    if permission_value:
        return name
    else:
        return ""
