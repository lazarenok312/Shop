from django import template

register = template.Library()


@register.filter
def humanize_price(value):
    try:
        return "{:,.2f}".format(float(value)).replace(",", " ")
    except (ValueError, TypeError):
        return value
