from django import template

register = template.Library()

@register.filter
def coma_point(value):
    return str(value).replace(",", ".")