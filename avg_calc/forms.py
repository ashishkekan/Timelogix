"""
Forms for handling user registration, work time entries, and other functionalities.
"""

import calendar
from datetime import datetime

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import WorkTimeEntry, SalaryExpenses, DailyWorkSummary, Leave, Task


class RegisterForm(UserCreationForm):
    """
    Form for user registration including email field.
    """
    email = forms.EmailField(required=True)

    class Meta:
        """
        Metadata for the RegisterForm.
        Specifies the model and fields to include in the form.
        """
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        """
        Save the user instance, adding the email field.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class WorkTimeEntryForm(forms.ModelForm):
    """
    Form for entering work time details.
    """
    date = forms.DateField(widget=forms.widgets.DateInput(attrs={"type": "date"}))

    class Meta:
        """
        Metadata for the WorkTimeEntryForm.
        Specifies the model and fields to include in the form, and custom widgets for time inputs.
        """
        model = WorkTimeEntry
        fields = ['date', 'login_time', 'logout_time', 'breakout_time', 'breakin_time']
        widgets = {
            'login_time': forms.TimeInput(format='%H:%M'),
            'logout_time': forms.TimeInput(format='%H:%M'),
            'breakout_time': forms.TimeInput(format='%H:%M'),
            'breakin_time': forms.TimeInput(format='%H:%M'),
        }


class UploadExcelForm(forms.Form):
    """
    Form for uploading an Excel file.
    """
    excel_file = forms.FileField(label='Upload Excel File')


class MonthChoiceForm(forms.Form):
    """
    Form for selecting a month.
    """
    month = forms.ChoiceField(
        choices=[(str(i), calendar.month_name[i]) for i in range(1, 13)],
        label="Select Month",
        initial=str(datetime.now().month)
    )


class DailyWorkSummaryForm(forms.ModelForm):
    """
    Form for summarizing daily work details.
    """
    class Meta:
        """
        Metadata for the DailyWorkSummaryForm.
        Specifies the model and fields to include in the form.
        """
        model = DailyWorkSummary
        fields = ['date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


class SalaryExpensesForm(forms.ModelForm):
    """
    Form for entering salary expenses.
    """
    class Meta:
        """
        Metadata for the SalaryExpensesForm.
        Specifies the model and fields to include in the form, and custom widgets for input fields.
        """
        model = SalaryExpenses
        fields = ['salary']
        widgets = {
            'salary': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }


class LeaveForm(forms.ModelForm):
    """
    Form for applying for leave.
    """
    class Meta:
        """
        Metadata for the LeaveForm.
        Specifies the model and fields to include in the form, and custom widgets for date inputs.
        """
        model = Leave
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class TaskForm(forms.ModelForm):
    """
    Form for managing tasks.
    """
    class Meta:
        """
        Metadata for the TaskForm.
        Specifies the model and fields to include in the form, and custom widgets for date and time inputs.
        """
        model = Task
        fields = [
            "task_name",
            "expected_time",
            "start_time",
            "total_hours",
            "expected_completion_date",
        ]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "expected_completion_date": forms.DateInput(attrs={"type": "date"}),
        }


class ChangePasswordForm(forms.Form):
    """
    Form for changing user password.
    """
    old_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")

    def clean(self):
        """
        Validate that new password and confirm password match.
        """
        super().clean()
        new_password = self.cleaned_data.get("new_password")
        confirm_password = self.cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error(
                'confirm_password',
                "New password and Confirm new password do not match!"
            )

        return self.cleaned_data
