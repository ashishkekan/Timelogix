from math import isnan

from babel.numbers import format_number
from django import template
from django.forms.boundfield import BoundField

register = template.Library()


@register.filter(name="format_duration")
def format_duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours} hrs, {minutes} mins"


@register.filter(name="add_class")
def add_class(field, css_class):
    if isinstance(field, BoundField):
        return field.as_widget(attrs={"class": css_class})
    return field


@register.filter(name="currency_format")
def currency_format(number, is_currency=False):
    if not number or (isinstance(number, float) and number != number):
        return "₹0" if is_currency else "0"
    try:
        if is_currency:
            locale.setlocale(locale.LC_ALL, "en_IN")
            formatted_number = intcomma(number)
            return f"₹{formatted_number}"
        return str(number)
    except Exception:
        return "-" if is_currency else "0"


@register.filter
def hours_minutes(td):
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{hours:02}:{minutes:02}"
