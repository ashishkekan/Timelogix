import pandas as pd
from datetime import timedelta, datetime

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import (
    WorkTimeEntryForm,
    UploadExcelForm,
    MonthChoiceForm,
    RegisterForm,
    SalaryExpensesForm,
    DailyWorkSummaryForm,
    LeaveForm,
    TaskForm, ChangePasswordForm, WorkTimeCalculationForm,
)
from .models import WorkTimeEntry, SalaryExpenses, DailyWorkSummary, Leave, Task, RecentActivity
from .templatetags.custom_filter import format_duration

TARGET_WORK_TIME = timedelta(hours=8, minutes=40)


def log_activity(user, description):
    RecentActivity.objects.create(user=user, description=description)


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activity(user, "Registered an account")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


def login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            log_activity(request.user, "Logged in")
            return redirect("dashboard")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})


def logout(request):
    auth_logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    if request.method == 'POST':
        if 'old_password' in request.POST:
            change_password_form = ChangePasswordForm(request.POST)
            if change_password_form.is_valid():
                old_password = change_password_form.cleaned_data.get('old_password')
                new_password = change_password_form.cleaned_data.get('new_password')
                if request.user.check_password(old_password):
                    request.user.set_password(new_password)
                    request.user.save()
                    log_activity(request.user, "Change Password")
                    update_session_auth_hash(request, request.user)
                    messages.success(request, 'Your password was successfully updated!')
                    log_activity(request.user, "Changed password")
                else:
                    messages.error(request, 'Current password is incorrect')
        else:
            request.user.first_name = request.POST.get('first_name', '')
            request.user.last_name = request.POST.get('last_name', '')
            request.user.email = request.POST.get('email', '')
            request.user.save()
            messages.success(request, 'Your details were successfully updated!')
            log_activity(request.user, "Updated profile details")

    recent_activities = RecentActivity.objects.filter(user=request.user).order_by('-timestamp')[:10]

    context = {
        'user': request.user,
        'recent_activities': recent_activities
    }
    return render(request, 'registration/profile.html', context)


@login_required
def submit_work_time(request):
    if request.method == "POST":
        form = WorkTimeEntryForm(request.POST)
        if form.is_valid():
            work_time_entry = form.save(commit=False)
            work_time_entry.user = request.user
            work_time_entry.save()
            log_activity(request.user, "Submit Worklog")
            return redirect("dashboard")
    else:
        form = WorkTimeEntryForm()
    return render(request, "worktime/submit_work_time.html", {"form": form})


@login_required
def download_template(request):
    df = pd.DataFrame(
        columns=["Date", "Login Time", "Logout Time", "Break-Out Time", "Break-In Time"]
    )
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="time_log_template.xlsx"'
    with pd.ExcelWriter(response, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Time Logs")

    return response


@login_required
def upload_time_logs(request):
    if request.method == "POST":
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES["excel_file"]
            data = pd.read_excel(excel_file)

            data["Date"] = pd.to_datetime(data["Date"], format="%d-%m-%Y").dt.date
            data["Login Time"] = pd.to_datetime(
                data["Login Time"], format="%H:%M:%S"
            ).dt.time
            data["Logout Time"] = pd.to_datetime(
                data["Logout Time"], format="%H:%M:%S"
            ).dt.time
            data["Break-Out Time"] = pd.to_datetime(
                data["Break-Out Time"], format="%H:%M:%S"
            ).dt.time
            data["Break-In Time"] = pd.to_datetime(
                data["Break-In Time"], format="%H:%M:%S"
            ).dt.time

            for _, row in data.iterrows():
                WorkTimeEntry.objects.create(
                    user=request.user,
                    date=row["Date"],
                    login_time=row["Login Time"],
                    logout_time=row["Logout Time"],
                    breakout_time=row["Break-Out Time"],
                    breakin_time=row["Break-In Time"],
                )
                log_activity(request.user, "Upload Work Time")

            return redirect("dashboard")
    else:
        form = UploadExcelForm()

    return render(request, "worktime/upload_time_logs.html", {"form": form})


@login_required
def dashboard(request):
    today = datetime.now().date()
    month_form = MonthChoiceForm(request.GET or None)
    selected_month = int(month_form.data.get("month", today.month))
    selected_year = today.year

    start_of_month = datetime(selected_year, selected_month, 1).date()
    end_of_month = start_of_month.replace(
        month=selected_month % 12 + 1, day=1
    ) - timedelta(days=1)

    leaves = Leave.objects.filter(
        user=request.user, start_date__lte=end_of_month, end_date__gte=start_of_month
    )

    leave_days = set()
    for leave in leaves:
        leave_days.update(
            [
                leave.start_date + timedelta(days=i)
                for i in range((leave.end_date - leave.start_date).days + 1)
            ]
        )

    entries = WorkTimeEntry.objects.filter(
        user=request.user, date__range=[start_of_month, end_of_month]
    ).exclude(date__in=leave_days)

    total_work_seconds = sum(
        entry.total_work_time.total_seconds()
        for entry in entries
        if entry.total_work_time
    )

    days_count = (end_of_month - start_of_month).days + 1
    weekdays = [
        start_of_month + timedelta(days=i)
        for i in range(days_count)
        if (start_of_month + timedelta(days=i)).weekday() not in {5, 6}
    ]

    weekdays = [day for day in weekdays if day not in leave_days]

    first_saturday = None
    third_saturday = None
    saturday_count = 0

    for day in weekdays:
        if day.weekday() == 5:
            saturday_count += 1
            if saturday_count == 1:
                first_saturday = day
            elif saturday_count == 3:
                third_saturday = day

    weekdays = [day for day in weekdays if day not in {first_saturday, third_saturday}]
    weekdays = [day for day in weekdays if day >= today]

    days_count = len(weekdays)
    average_work_seconds = total_work_seconds / days_count if days_count else 0

    additional_seconds_per_day = 0
    need_time = 0
    if average_work_seconds < TARGET_WORK_TIME.total_seconds():
        total_target_seconds = TARGET_WORK_TIME.total_seconds() * days_count
        time_difference_seconds = total_target_seconds - total_work_seconds
        additional_seconds_per_day = time_difference_seconds / days_count
        need_time = (additional_seconds_per_day / 60)

    average_time_needed_to_work = need_time / 60
    average_time = total_work_seconds / len(entries) if entries else 0

    context = {
        "month_form": month_form,
        "entries": entries,
        "total_work_time": format_duration(total_work_seconds),
        "average_work_time": format_duration(average_work_seconds),
        "additional_time_per_day": format_duration(additional_seconds_per_day),
        "target_met": total_work_seconds >= TARGET_WORK_TIME.total_seconds(),
        "leaves": leaves,
        "average_time": format_duration(average_time),
        "time_needed": format_duration(average_time_needed_to_work),
    }
    return render(request, "worktime/dashboard.html", context)


@login_required
def total_expenses(request):
    user = request.user
    profile = SalaryExpenses.objects.get(user=user)
    month_form = MonthChoiceForm(request.GET or None)

    today = datetime.now().date()
    selected_month = int(request.GET.get("month", today.month))
    selected_year = int(request.GET.get("year", today.year))

    start_of_month = datetime(selected_year, selected_month, 1).date()
    end_of_month = start_of_month.replace(
        month=selected_month % 12 + 1, day=1
    ) - timedelta(days=1)

    entries = WorkTimeEntry.objects.filter(
        user=user, date__range=[start_of_month, end_of_month]
    )
    total_lunch_expenses = entries.count() * 50

    pf = 200
    payment = profile.salary - pf

    balance = payment - total_lunch_expenses

    context = {
        "salary": payment,
        "pf": pf,
        "entries": entries,
        "total_lunch_expenses": total_lunch_expenses,
        "balance": balance,
        "month": start_of_month.strftime("%B %Y"),
        "month_form": month_form,
    }
    return render(request, "worktime/total_expenses.html", context)


@login_required
def update_salary_expenses(request):
    user = request.user
    try:
        profile = SalaryExpenses.objects.get(user=user)
    except SalaryExpenses.DoesNotExist:
        profile = None

    if request.method == 'POST':
        form = SalaryExpensesForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            log_activity(request.user, "Update salary")
            return redirect('salary_expenses_success')
    else:
        form = SalaryExpensesForm(instance=profile)

    return render(request, 'worktime/update_salary_expenses.html', {'form': form})


def salary_expenses_success(request):
    return render(request, 'worktime/success.html')


@login_required
def calculate_work_time(request):
    if request.method == "POST":
        form = DailyWorkSummaryForm(request.POST)
        if form.is_valid():
            summary = form.save(commit=False)
            summary.user = request.user

            selected_date = summary.date
            entries = WorkTimeEntry.objects.filter(
                user=request.user, date=selected_date
            )

            total_work_seconds = sum(
                entry.total_work_time.total_seconds()
                for entry in entries
                if entry.total_work_time
            )

            days_count = entries.count()
            average_work_seconds = total_work_seconds / days_count if days_count else 0

            additional_seconds_needed = 0
            if average_work_seconds < TARGET_WORK_TIME.total_seconds():
                additional_seconds_needed = (
                    TARGET_WORK_TIME.total_seconds() - average_work_seconds
                )

            summary.average_work_time = timedelta(seconds=average_work_seconds)
            summary.additional_time_needed = timedelta(
                seconds=additional_seconds_needed
            )
            summary.save()
            log_activity(request.user, "Calculate Work Time")
            return redirect("work_summary_detail", pk=summary.pk)
    else:
        form = DailyWorkSummaryForm()

    return render(request, "worktime/calculate_work_time.html", {"form": form})


@login_required
def work_summary_detail(request, pk):
    summary = DailyWorkSummary.objects.get(pk=pk)
    return render(
        request,
        "worktime/work_summary_detail.html",
        {"summary": summary}
    )


@login_required
def add_leave(request):
    if request.method == "POST":
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.user = request.user
            leave.save()
            log_activity(request.user, "Apply Leave")
            return redirect("dashboard")
    else:
        form = LeaveForm()
    return render(request, "worktime/add_leave.html", {"form": form})


@login_required()
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            log_activity(request.user, "Create Task")
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'worktime/task_form.html', {'form': form})


@login_required()
def task_list(request):
    tasks = Task.objects.filter(user=request.user)
    return render(request, 'worktime/task_list.html', {'tasks': tasks})


@login_required()
def calculate_working_hours(request):
    if request.method == "POST":
        form = WorkTimeCalculationForm(request.POST)
        if form.is_valid():
            current_avg = form.cleaned_data["current_avg"]
            leave_days = form.cleaned_data["leave_days"]

            today = datetime.today()
            total_days_in_month = (
                (datetime(today.year, today.month + 1, 1) - timedelta(days=1)).day
                if today.month != 12
                else 31
            )
            sundays = sum(
                1
                for day in range(1, total_days_in_month + 1)
                if datetime(today.year, today.month, day).weekday() == 6
            )
            saturdays = [
                datetime(today.year, today.month, day)
                for day in range(1, total_days_in_month + 1)
                if datetime(today.year, today.month, day).weekday() == 5
            ]
            first_third_saturdays = sum(
                1 for i, saturday in enumerate(saturdays) if i == 0 or i == 2
            )

            total_leave_days = sundays + first_third_saturdays + leave_days
            working_days = total_days_in_month - total_leave_days
            completed_days = today.day - total_leave_days
            remaining_days = working_days - completed_days
            total_required_hours = working_days * 8.67
            total_worked_hours = current_avg * completed_days
            remaining_required_hours = total_required_hours - total_worked_hours

            if remaining_days > 0:
                required_daily_hours = remaining_required_hours / remaining_days
            else:
                required_daily_hours = 0

            calculation = form.save(commit=False)
            calculation.required_daily_hours = round(required_daily_hours, 2)
            calculation.remaining_required_hours = round(remaining_required_hours, 2)
            calculation.save()

            return render(
                request,
                "worktime/work_api.html",
                {
                    "form": form,
                    "required_daily_hours": round(required_daily_hours, 2),
                    "remaining_required_hours": round(remaining_required_hours, 2),
                },
            )
    else:
        form = WorkTimeCalculationForm()

    return render(request, "worktime/work_api.html", {"form": form})
