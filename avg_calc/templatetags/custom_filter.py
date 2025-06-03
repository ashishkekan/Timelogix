from math import isnan

from babel.numbers import format_number
from django import template

register = template.Library()


@register.filter(name="format_duration")
def format_duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours} hours, {minutes} minutes"


@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})


@register.filter(name="currency_format")
def currency_format(number):
    if not number or (isinstance(number, float) and isnan(number)):
        return "₹0"
    try:
        indian_currency_format = format_number(number, locale="en_IN")
    except Exception:
        return "-"
    return "₹" + str(indian_currency_format)
