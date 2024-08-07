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
    TaskForm, ChangePasswordForm,
)
from .models import WorkTimeEntry, SalaryExpenses, DailyWorkSummary, Leave, Task, RecentActivity
from .templatetags.custom_filter import format_duration

TARGET_WORK_TIME = timedelta(hours=8, minutes=40)


def log_activity(user, description):
    """
    Log recent activity for a user.

    Args:
        user (User): The user who performed the activity.
        description (str): A description of the activity.
    """
    RecentActivity.objects.create(user=user, description=description)


def register(request):
    """
    Handle user registration.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The registration page or a redirect to the login page.
    """
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
    """
    Handle user login.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The login page or a redirect to the dashboard.
    """
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
    """
    Handle user logout.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: A redirect to the login page.
    """
    auth_logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    """
    Display and update user profile details.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The profile page with recent activities.
    """
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
    """
    Handle submission of work time entries.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The work time submission page or a redirect to the dashboard.
    """
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
    """
    Download a template for time log entries.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: An Excel file response with the time log template.
    """
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
    """
    Handle upload of time log entries from an Excel file.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The time log upload page or a redirect to the dashboard.
    """
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
    """
    Display the user's work time dashboard.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The dashboard page.
    """
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

    days_count = len(weekdays)
    average_work_seconds = total_work_seconds / days_count if days_count else 0

    additional_seconds_per_day = 0
    if average_work_seconds < TARGET_WORK_TIME.total_seconds():
        remaining_seconds = TARGET_WORK_TIME.total_seconds() - average_work_seconds
        additional_seconds_per_day = remaining_seconds / days_count if days_count else 0

    tasks = Task.objects.filter(user=request.user, status='Pending')
    total_hours = timedelta(hours=0)

    for task in tasks:
        total_hours += task.expected_time

    task_form = TaskForm()
    return render(
        request,
        "dashboard.html",
        {
            "total_work_time": format_duration(timedelta(seconds=total_work_seconds)),
            "target_work_time": format_duration(TARGET_WORK_TIME),
            "additional_time": format_duration(
                timedelta(seconds=additional_seconds_per_day)
            ),
            "month_form": month_form,
            "task_form": task_form,
            "tasks": tasks,
            "total_hours": total_hours,
        },
    )


@login_required
def daily_summary(request):
    """
    Display and handle daily work summary submissions.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The daily work summary page or a redirect to the same page.
    """
    if request.method == "POST":
        form = DailyWorkSummaryForm(request.POST)
        if form.is_valid():
            daily_work_summary = form.save(commit=False)
            daily_work_summary.user = request.user
            daily_work_summary.save()
            log_activity(request.user, "Submitted Daily Work Summary")
            return redirect("daily_summary")
    else:
        form = DailyWorkSummaryForm()

    today = datetime.now().date()
    entries = WorkTimeEntry.objects.filter(user=request.user, date=today)

    total_work_seconds = sum(
        entry.total_work_time.total_seconds()
        for entry in entries
        if entry.total_work_time
    )

    total_work_time = timedelta(seconds=total_work_seconds)

    return render(
        request,
        "worktime/daily_summary.html",
        {"form": form, "total_work_time": format_duration(total_work_time)},
    )


@login_required
def add_salary_expenses(request):
    """
    Handle submission of salary expenses.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The salary expenses submission page or a redirect to the dashboard.
    """
    if request.method == "POST":
        form = SalaryExpensesForm(request.POST)
        if form.is_valid():
            salary_expense = form.save(commit=False)
            salary_expense.user = request.user
            salary_expense.save()
            log_activity(request.user, "Added Salary Expenses")
            return redirect("dashboard")
    else:
        form = SalaryExpensesForm()
    return render(request, "salary_expenses/add_salary_expenses.html", {"form": form})


@login_required
def add_leave(request):
    """
    Handle leave requests submission.

    Args:
        request (HttpRequest): The request object.

    Returns:
        HttpResponse: The leave request submission page or a redirect to the dashboard.
    """
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.user = request.user
            leave.save()
            log_activity(request.user, "Added Leave")
            return redirect('dashboard')
    else:
        form = LeaveForm()
    return render(request, 'leave/add_leave.html', {'form': form})
