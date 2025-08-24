from django import template

register = template.Library()


@register.filter
def humanize_price(value):
    try:
        return "{:,.2f}".format(float(value)).replace(",", " ")
    except (ValueError, TypeError):
        return value


@register.filter
def dict_get(d, key):
    if not d:
        return 0
    return d.get(key, 0)
