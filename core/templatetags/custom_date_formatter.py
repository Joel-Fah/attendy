from django import template
import datetime

register = template.Library()


@register.filter
def format_date(value):
    if isinstance(value, datetime.date):
        return value.strftime('%a. %d %b %Y')
    return value
