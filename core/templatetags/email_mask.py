from django import template

register = template.Library()


@register.filter(name='mask_email')
def mask_email(email):
    try:
        username, domain = email.split('@')
        masked_username = username[:2] + '*' * (len(username) - 2)
        domain_name, domain_extension = domain.split('.')
        masked_domain = domain_name[:2] + '*' * (len(domain_name) - 2) + '.' + domain_extension
        return f'{masked_username}@{masked_domain}'
    except ValueError:
        return email
