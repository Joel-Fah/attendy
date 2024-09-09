from django import template
from django.utils.timezone import now, is_aware, make_aware
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def time_ago(value):
    if not value:
        return ""

    # Ensure value is a datetime object
    if not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())

    # Ensure both datetimes are offset-aware
    current_time = now()
    if not is_aware(value):
        value = make_aware(value)
    if not is_aware(current_time):
        current_time = make_aware(current_time)

    delta = current_time - value

    if delta < timedelta(minutes=1):
        return "just now"
    elif delta < timedelta(hours=1):
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif delta < timedelta(days=1):
        hours = int(delta.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif delta < timedelta(days=30):
        days = delta.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif delta < timedelta(days=365):
        months = delta.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = delta.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"