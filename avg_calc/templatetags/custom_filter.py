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
