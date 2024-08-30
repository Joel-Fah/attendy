# core/templatetags/number_formatting.py

from django import template

register = template.Library()


@register.filter
def thousand_separator(value):
    try:
        return "{:,}".format(value)
    except (ValueError, TypeError):
        return value
