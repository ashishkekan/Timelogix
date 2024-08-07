"""
Django application configuration for the AvgCalc app.
"""

from django.apps import AppConfig


class AvgCalcConfig(AppConfig):
    """
    Configuration for the AvgCalc application.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "avg_calc"
