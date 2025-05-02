import calendar
from datetime import datetime

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import DailyWorkSummary, Leave, SalaryExpenses, Task, WorkTimeEntry


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class WorkTimeEntryForm(forms.ModelForm):
    date = forms.DateField(widget=forms.widgets.DateInput(attrs={"type": "date"}))

    class Meta:
        model = WorkTimeEntry
        fields = ["date", "login_time", "logout_time", "breakout_time", "breakin_time"]
        widgets = {
            "login_time": forms.TimeInput(format="%H:%M"),
            "logout_time": forms.TimeInput(format="%H:%M"),
            "breakout_time": forms.TimeInput(format="%H:%M"),
            "breakin_time": forms.TimeInput(format="%H:%M"),
        }


class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(label="Upload Excel File")


class MonthChoiceForm(forms.Form):
    month = forms.ChoiceField(
        choices=[(str(i), calendar.month_name[i]) for i in range(1, 13)],
        label="Select Month",
        initial=str(datetime.now().month),
    )


class DailyWorkSummaryForm(forms.ModelForm):
    class Meta:
        model = DailyWorkSummary
        fields = ["date"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }


class SalaryExpensesForm(forms.ModelForm):
    class Meta:
        model = SalaryExpenses
        fields = ["salary"]
        widgets = {
            "salary": forms.NumberInput(
                attrs={"step": "0.01", "class": "form-control"}
            ),
        }


class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ["start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
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
    old_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label="Confirm New Password"
    )

    def clean(self):
        super().clean()
        new_password = self.cleaned_data.get("new_password")
        confirm_password = self.cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error(
                "confirm_password",
                "New password and Confirm new password do not match!",
            )

        return self.cleaned_data
