from datetime import datetime

from django.contrib.auth.models import User
from django.db import models


class SalaryExpenses(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.user.username


class WorkTimeEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    login_time = models.TimeField()
    logout_time = models.TimeField()
    breakout_time = models.TimeField()
    breakin_time = models.TimeField()
    total_work_time = models.DurationField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    def save(self, *args, **kwargs):
        login_datetime = datetime.combine(self.date, self.login_time)
        logout_datetime = datetime.combine(self.date, self.logout_time)
        breakout_datetime = datetime.combine(self.date, self.breakout_time)
        breakin_datetime = datetime.combine(self.date, self.breakin_time)

        work_duration = (logout_datetime - login_datetime) - (breakin_datetime - breakout_datetime)
        self.total_work_time = work_duration

        super().save(*args, **kwargs)


class DailyWorkSummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    average_work_time = models.DurationField()
    additional_time_needed = models.DurationField()

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class Leave(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.username} - {self.start_date} to {self.end_date}"


class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=255)
    expected_time = models.DurationField()
    start_time = models.DateTimeField()
    total_hours = models.FloatField()
    expected_completion_date = models.DateField()

    def __str__(self):
        return self.task_name
