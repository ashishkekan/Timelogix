from django.contrib import admin

from .models import SalaryExpenses, WorkTimeEntry

admin.site.register(WorkTimeEntry)
admin.site.register(SalaryExpenses)
