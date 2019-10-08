from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    a = Decimal.from_float(arg)
    return round(value*a,2)

@register.filter(name='add')
def multiply(value, arg):
    a = Decimal.from_float(arg)
    return value+a