"""
This module registers Django admin interfaces for the WorkTimeEntry and SalaryExpenses models.
"""

from django.contrib import admin
from .models import WorkTimeEntry, SalaryExpenses

admin.site.register(WorkTimeEntry)
admin.site.register(SalaryExpenses)
