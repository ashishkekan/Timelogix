"""
Custom template filters for the avg_calc application.
"""

from django import template

register = template.Library()


@register.filter(name="format_duration")
def format_duration(seconds):
    """
    Format a duration given in seconds into a string with hours and minutes.

    Args:
        seconds (int): The duration in seconds.

    Returns:
        str: The formatted duration as "X hours, Y minutes".
    """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours} hours, {minutes} minutes"
