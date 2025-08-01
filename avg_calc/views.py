from calendar import monthrange
from datetime import date, datetime, time, timedelta

import pandas as pd
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import CharField, Count, Sum, Value
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.timezone import is_naive, localtime, make_aware
from django.views.decorators.http import require_POST
from xhtml2pdf import pisa

from avg_calc.forms import (
    ChangePasswordForm,
    DailyWorkSummaryForm,
    LeaveForm,
    MonthChoiceForm,
    RegisterForm,
    SalaryExpensesForm,
    TaskForm,
    UploadExcelForm,
    UserEditForm,
    WorkTimeEntryForm,
)
from avg_calc.methods import (
    get_admin_stats,
    get_quick_actions,
    get_target_status,
    get_user_stats,
    home_context,
    log_activity,
)
from avg_calc.models import (
    DailyWorkSummary,
    Leave,
    RecentActivity,
    SalaryExpenses,
    Task,
    User,
    WorkTimeEntry,
)
from avg_calc.templatetags.custom_filter import format_duration

TARGET_WORK_TIME = timedelta(hours=8, minutes=40)

username = "test"
password = "Lemon@123"


def safe_localtime(time_obj, date_obj=None):
    if time_obj is None:
        return ""

    # If only time is provided, combine with date (if available)
    if isinstance(time_obj, time) and date_obj:
        dt = datetime.combine(date_obj, time_obj)
    elif isinstance(time_obj, datetime):
        dt = time_obj
    else:
        return str(time_obj)

    if is_naive(dt):
        dt = make_aware(dt)

    return localtime(dt).strftime("%H:%M")


def home(request):
    """
    Renders the TimeLogix homepage with dynamic content.

    Returns:
        HttpResponse: Rendered homepage template with content dictionaries.
    """

    return render(request, "worktime/home.html", home_context)


def demo_login(request):
    """
    Logs in a test user for the Live Demo and redirects to the dashboard.

    Uses hardcoded credentials for the test user (username: test, password: Lemon@123).
    Logs the activity and shows a success message.

    Returns:
        HttpResponseRedirect: Redirects to the dashboard if login is successful, or to the login page if authentication fails.
    """

    user = authenticate(request, username=username, password=password)
    if user is not None:
        auth_login(request, user)
        log_activity(user, "Logged in via Live Demo")
        messages.success(request, "Logged in as demo user!")
        return redirect("dashboard")
    else:
        messages.error(
            request, "Demo login failed. Please try again or contact support."
        )
        return redirect("login")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activity(user, "Registered an account")
            messages.success(request, "User registered successfully!")
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
            messages.success(request, "User Login successfully!")
            return redirect("dashboard")
    else:
        form = AuthenticationForm()
    return render(request, "registration/login.html", {"form": form})


def logout(request):
    auth_logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    user_form = UserEditForm(instance=request.user)
    password_form = ChangePasswordForm()

    if request.method == "POST":
        if "change_password" in request.POST:
            password_form = ChangePasswordForm(request.POST)
            if password_form.is_valid():
                old_password = password_form.cleaned_data.get("old_password")
                new_password = password_form.cleaned_data.get("new_password")
                if request.user.check_password(old_password):
                    request.user.set_password(new_password)
                    request.user.save()
                    RecentActivity.objects.create(
                        user=request.user, description="Changed password"
                    )
                    update_session_auth_hash(request, request.user)
                    messages.success(request, "Your password was successfully updated!")
                else:
                    messages.error(request, "Current password is incorrect.")
            else:
                messages.error(
                    request, "Please correct the errors in the password form."
                )
        elif "update_details" in request.POST:
            user_form = UserEditForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                RecentActivity.objects.create(
                    user=request.user, description="Updated profile details"
                )
                messages.success(request, "Your details were successfully updated!")
            else:
                messages.error(
                    request, "Please correct the errors in the profile form."
                )
        return redirect("profile")

    context = {
        "user_form": user_form,
        "password_form": password_form,
        "user": request.user,
    }
    return render(request, "registration/profile.html", context)


@login_required
def create_timelogs(request):
    if request.method == "POST":
        form = WorkTimeEntryForm(request.POST)
        if form.is_valid():
            work_time_entry = form.save(commit=False)
            work_time_entry.user = request.user
            work_time_entry.save()
            log_activity(request.user, "Submit Timelogs")
            messages.success(request, "Timelog submitted successfully!")
            return redirect("create-timelogs")
    else:
        form = WorkTimeEntryForm()
    return render(request, "worktime/submit_work_time.html", {"form": form})


@login_required
def export_template(request):
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
        form = UploadExcelForm(request.POST or None, request.FILES or None)
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
            messages.success(request, "Timelogs uploaded successfully!")
            return redirect("dashboard")
    else:
        form = UploadExcelForm()

    return render(request, "worktime/upload_time_logs.html", {"form": form})


@login_required
def dashboard(request):
    today = datetime.now().date()
    month_form = MonthChoiceForm(request.GET or None)
    selected_month = int(month_form.data.get("month", today.month))
    selected_year = int(month_form.data.get("year", today.year))

    start_of_month = datetime(selected_year, selected_month, 1).date()
    end_of_month = start_of_month.replace(
        month=(selected_month % 12) + 1 if selected_month < 12 else 1,
        year=selected_year + 1 if selected_month == 12 else selected_year,
        day=1,
    ) - timedelta(days=1)

    # Get leaves
    leaves = Leave.objects.filter(
        user=request.user,
        start_date__lte=end_of_month,
        end_date__gte=start_of_month,
    )

    leave_days = set()
    for leave in leaves:
        leave_days.update(
            [
                leave.start_date + timedelta(days=i)
                for i in range((leave.end_date - leave.start_date).days + 1)
            ]
        )

    # Generate all days in month
    days_count = (end_of_month - start_of_month).days + 1
    all_days = [start_of_month + timedelta(days=i) for i in range(days_count)]

    # Identify excluded Saturdays
    saturdays = [day for day in all_days if day.weekday() == 5]
    excluded_saturdays = set()
    if len(saturdays) >= 1:
        excluded_saturdays.add(saturdays[0])  # 1st Saturday
    if len(saturdays) >= 3:
        excluded_saturdays.add(saturdays[2])  # 3rd Saturday

    # Final working days
    final_days = [
        day
        for day in all_days
        if day.weekday() != 6
        and day not in excluded_saturdays
        and day not in leave_days
    ]

    entries = WorkTimeEntry.objects.filter(
        user=request.user, date__range=[start_of_month, end_of_month]
    ).exclude(date__in=leave_days)

    total_work_seconds = sum(
        entry.total_work_time.total_seconds()
        for entry in entries
        if entry.total_work_time
    )

    working_days_count = len(final_days)
    average_work_seconds = (
        total_work_seconds / working_days_count if working_days_count else 0
    )

    # Assuming TARGET_WORK_TIME is defined in settings or as a constant
    TARGET_WORK_TIME = timedelta(hours=8, minutes=40)

    additional_seconds_per_day = 0
    need_time = 0
    overtime = 0
    if (
        working_days_count > 0
        and average_work_seconds < TARGET_WORK_TIME.total_seconds()
    ):
        total_target_seconds = TARGET_WORK_TIME.total_seconds() * working_days_count
        time_difference_seconds = total_target_seconds - total_work_seconds
        additional_seconds_per_day = time_difference_seconds / days_count
        need_time = additional_seconds_per_day / 60
    elif working_days_count > 0:
        total_target_seconds = TARGET_WORK_TIME.total_seconds() * working_days_count
        additional_overtime = total_work_seconds - total_target_seconds
        overtime = (additional_overtime / days_count) / 60

    average_time = total_work_seconds / len(entries) if entries else 0

    # Dynamic stat cards for user dashboard
    user_stats = get_user_stats(entries, total_work_seconds, need_time, average_time)

    # Dynamic target status
    target_status = get_target_status(
        average_time, TARGET_WORK_TIME.total_seconds(), need_time
    )

    # Admin dashboard stats
    total_users = User.objects.count()
    total_worklogs = WorkTimeEntry.objects.count()
    total_expenses = SalaryExpenses.objects.aggregate(total=Sum("salary"))["total"] or 0
    total_tasks = Task.objects.count()
    total_leaves = Leave.objects.count()

    admin_stats = get_admin_stats(
        total_users, total_worklogs, total_expenses, total_tasks, total_leaves
    )

    # Quick actions (already in view, reused)
    quick_actions = get_quick_actions()

    # Top 3 active users (based on recent activity count)
    top_3_active_users = (
        User.objects.annotate(activity_count=Count("recentactivity"))
        .order_by("-activity_count")[:3]
        .values(
            "username",
            activity_description=Value(
                "Most active this week", output_field=CharField()
            ),
        )
    )

    context = {
        "dashboard_title": "My Dashboard" if not request.user.is_staff else "Dashboard",
        "dashboard_subtitle": (
            f"Welcome back, {request.user.username}!"
            if not request.user.is_staff
            else "Overview of your organization's time tracking metrics."
        ),
        "month_form": month_form,
        "user_stats": user_stats,
        "quick_actions": quick_actions,
        "target_status": target_status,
        "admin_stats": admin_stats,
        "top_3_recent_activity": RecentActivity.objects.order_by("-timestamp")[:3],
        "top_3_active_users": top_3_active_users,
    }

    return render(request, "worktime/dashboard.html", context)


@login_required
def total_expenses(request):
    today = datetime.now().date()
    month_form = MonthChoiceForm(request.GET or None)

    selected_month = (
        int(request.GET.get("month", today.month))
        if month_form.is_valid()
        else today.month
    )
    selected_year = (
        int(request.GET.get("year", today.year))
        if month_form.is_valid()
        else today.year
    )

    start_of_month = datetime(selected_year, selected_month, 1).date()
    end_of_month = start_of_month.replace(
        month=selected_month % 12 + 1, day=1
    ) - timedelta(days=1)

    context = {
        "month": start_of_month.strftime("%B %Y"),
        "month_form": month_form,
        "entries": [],
        "salary": 0,
        "pf": 0,
        "total_lunch_expenses": 0,
        "balance": 0,
        "no_data": False,
    }

    if request.user.is_staff:
        selected_user_id = (
            month_form.data.get("user") if month_form.is_valid() else None
        )
        if selected_user_id:
            try:
                target_user = User.objects.get(id=selected_user_id)
                profile = SalaryExpenses.objects.filter(user=target_user).first()
                if profile:
                    entries = WorkTimeEntry.objects.filter(
                        user=target_user, date__range=[start_of_month, end_of_month]
                    )
                    total_lunch_expenses = entries.count() * 50
                    pf = 200
                    payment = profile.salary - pf
                    balance = payment - total_lunch_expenses
                    context.update(
                        {
                            "entries": entries,
                            "salary": payment,
                            "pf": pf,
                            "total_lunch_expenses": total_lunch_expenses,
                            "balance": balance,
                        }
                    )
                else:
                    context["no_data"] = True
            except User.DoesNotExist:
                context["no_data"] = True
        else:
            profiles = SalaryExpenses.objects.filter(user__is_superuser=False)
            if profiles.exists():
                entries = WorkTimeEntry.objects.filter(
                    date__range=[start_of_month, end_of_month], user__is_superuser=False
                )
                total_lunch_expenses = entries.count() * 50
                total_salary = sum(profile.salary for profile in profiles)
                total_pf = profiles.count() * 200
                total_payment = total_salary - total_pf
                balance = total_payment - total_lunch_expenses
                context.update(
                    {
                        "entries": entries,
                        "salary": total_payment,
                        "pf": total_pf,
                        "total_lunch_expenses": total_lunch_expenses,
                        "balance": balance,
                    }
                )
            else:
                context["no_data"] = True
    else:
        profile = SalaryExpenses.objects.filter(user=request.user).first()
        if profile:
            entries = WorkTimeEntry.objects.filter(
                user=request.user, date__range=[start_of_month, end_of_month]
            )
            total_lunch_expenses = entries.count() * 50
            pf = 200
            payment = profile.salary - pf
            balance = payment - total_lunch_expenses
            context.update(
                {
                    "entries": entries,
                    "salary": payment,
                    "pf": pf,
                    "total_lunch_expenses": total_lunch_expenses,
                    "balance": balance,
                }
            )
        else:
            context["no_data"] = True

    # Paginate entries
    paginator = Paginator(context["entries"], 10)
    page_number = request.GET.get("page")
    context["entries"] = paginator.get_page(page_number)

    return render(request, "worktime/total_expenses.html", context)


@login_required
def update_salary_expenses(request):
    user = request.user
    try:
        profile = SalaryExpenses.objects.get(user=user)
    except SalaryExpenses.DoesNotExist:
        profile = None

    if request.method == "POST":
        form = SalaryExpensesForm(request.POST, instance=profile)
        if form.is_valid():
            salary = form.save(commit=False)
            salary.user = request.user
            salary.save()
            log_activity(request.user, "Update salary")
            messages.success(request, "Salary Expenses are submitted successfully!")
            return redirect("create-expenses")
    else:
        form = SalaryExpensesForm(instance=profile)

    return render(request, "worktime/update_salary_expenses.html", {"form": form})


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
            return redirect("time-details", pk=summary.pk)
    else:
        form = DailyWorkSummaryForm()

    return render(request, "worktime/calculate_work_time.html", {"form": form})


@login_required
def work_summary_detail(request, pk):
    """Display detailed work summary with stat cards."""
    try:
        summary = DailyWorkSummary.objects.get(pk=pk)
    except DailyWorkSummary.DoesNotExist:
        raise Http404("Work summary does not exist")

    stat_cards = [
        {
            "title": "Date",
            "value": summary.date,
            "icon_class": "fas fa-calendar-alt",
            "icon_color": "text-purple-500",
        },
        {
            "title": "Average Work Time",
            "value": summary.average_work_time,
            "icon_class": "fas fa-clock",
            "icon_color": "text-indigo-500",
        },
        {
            "title": "Additional Time Needed",
            "value": summary.additional_time_needed,
            "icon_class": "fas fa-chart-line",
            "icon_color": "text-teal-500",
        },
    ]

    return TemplateResponse(
        request,
        "worktime/work_summary_detail.html",
        {
            "summary": summary,
            "stat_cards": stat_cards,
            "username": request.user.username,
        },
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
            messages.success(request, "Leave added successfully!")
            return redirect("dashboard")
    else:
        form = LeaveForm()
    return render(request, "worktime/add_leave.html", {"form": form})


@login_required()
def create_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            log_activity(request.user, "Create Task")
            messages.success(request, "Task added successfully!")
            return redirect("task-list")
    else:
        form = TaskForm()
    return render(request, "worktime/task_form.html", {"form": form})


@login_required()
def task_list(request):
    if not request.user.is_staff:
        tasks = Task.objects.filter(user=request.user)
    else:
        tasks = Task.objects.all()
    return render(request, "worktime/task_list.html", {"tasks": tasks})


@login_required()
def recent_activity(request):
    activities = RecentActivity.objects.filter(user=request.user).order_by("-timestamp")

    paginator = Paginator(activities, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }
    return render(request, "worktime/recent_activity.html", context)


@login_required
def work_view(request):
    today = datetime.now().date()
    month_form = MonthChoiceForm(request.GET or None)

    # Extract month/year, with validation
    selected_month = (
        int(month_form.data.get("month", today.month))
        if month_form.is_valid()
        else today.month
    )
    selected_year = today.year

    # Calculate date range for the selected month
    start_of_month = datetime(selected_year, selected_month, 1).date()
    end_of_month = start_of_month.replace(
        month=selected_month % 12 + 1, day=1
    ) - timedelta(days=1)

    # Get leave days for the relevant user
    if request.user.is_staff:
        selected_user_id = (
            month_form.data.get("user") if month_form.is_valid() else None
        )
        target_user = (
            User.objects.get(id=selected_user_id) if selected_user_id else request.user
        )
    else:
        target_user = request.user

    leaves = Leave.objects.filter(
        user=target_user, start_date__lte=end_of_month, end_date__gte=start_of_month
    )
    leave_days = set()
    for leave in leaves:
        leave_days.update(
            leave.start_date + timedelta(days=i)
            for i in range((leave.end_date - leave.start_date).days + 1)
        )

    # Filter work time entries
    if request.user.is_staff:
        selected_user_id = (
            month_form.data.get("user") if month_form.is_valid() else None
        )
        if selected_user_id:
            # Filter by selected user
            all_entries = (
                WorkTimeEntry.objects.filter(
                    user_id=selected_user_id, date__range=[start_of_month, end_of_month]
                )
                .exclude(date__in=leave_days)
                .order_by("date")
            )
        else:
            # Show all users' entries
            all_entries = (
                WorkTimeEntry.objects.filter(date__range=[start_of_month, end_of_month])
                .exclude(date__in=leave_days)
                .order_by("date")
            )
    else:
        # Non-staff users see only their own entries
        all_entries = (
            WorkTimeEntry.objects.filter(
                user=request.user, date__range=[start_of_month, end_of_month]
            )
            .exclude(date__in=leave_days)
            .order_by("date")
        )

    # Paginate entries
    paginator = Paginator(all_entries, 10)
    page_number = request.GET.get("page")
    entries = paginator.get_page(page_number)

    return render(
        request,
        "worktime/work-list.html",
        {"entries": entries, "month_form": month_form},
    )


@login_required
def edit_timelogs(request, pk):
    entry = None
    if request.user.is_staff:
        entry = get_object_or_404(WorkTimeEntry, pk=pk)
    else:
        entry = get_object_or_404(WorkTimeEntry, pk=pk, user=request.user)

    if request.method == "POST":
        form = WorkTimeEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, "Work entry updated successfully.")
            return redirect("worktime")
    else:
        form = WorkTimeEntryForm(instance=entry)

    return render(request, "worktime/work-edit.html", {"form": form, "entry": entry})


@login_required
def delete_timelogs(request, pk):
    if request.user.is_staff:
        entry = get_object_or_404(WorkTimeEntry, pk=pk)
    else:
        entry = get_object_or_404(WorkTimeEntry, pk=pk, user=request.user)

    if request.method == "POST":
        entry.delete()
        messages.success(request, "Work entry deleted successfully.")
        return redirect("worktime")

    return render(request, "worktime/work-list.html", {"entry": entry})


@login_required
def leaves(request):
    form = MonthChoiceForm(request.GET or None)

    # Default to current month and year
    today = date.today()
    default_month = today.month
    default_year = today.year

    # Fetch all leaves (admin) or only for logged-in user
    leaves = (
        Leave.objects.all()
        if request.user.is_staff
        else Leave.objects.filter(user=request.user)
    )

    if form.is_valid():
        month = form.cleaned_data.get("month") or default_month
        year = form.cleaned_data.get("year") or default_year
        selected_user = (
            form.cleaned_data.get("user") if request.user.is_staff else request.user
        )
    else:
        month = default_month
        year = default_year
        selected_user = request.user

    # Date range for selected month
    start_date = date(int(year), int(month), 1)
    end_date = date(int(year), int(month), monthrange(int(year), int(month))[1])

    leaves = leaves.filter(start_date__lte=end_date, end_date__gte=start_date)

    if request.user.is_staff and selected_user:
        leaves = leaves.filter(user=selected_user)

    return render(
        request,
        "worktime/leaves.html",
        {
            "leaves": leaves,
            "month_form": form,
            "selected_month": month,
            "selected_year": year,
        },
    )


@login_required
def users(request):
    users = User.objects.all().order_by("id")
    paginator = Paginator(users, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "users": users,
        "page_obj": page_obj,
    }
    return render(request, "worktime/users.html", context)


@login_required
def edit_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect("user-list")
    else:
        form = UserEditForm(instance=user_obj)

    return render(
        request, "worktime/edit-user.html", {"form": form, "user_obj": user_obj}
    )


@login_required
def delete_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user_obj.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("user-list")
    return render(request, "worktime/users.html", {"user_obj": user_obj})


@login_required
def export_worklog(request):
    today = datetime.now().date()
    selected_month = int(request.GET.get("month", today.month))
    selected_year = today.year
    user_id = request.GET.get("user")

    if request.user.is_staff and user_id:
        user = get_object_or_404(User, id=user_id)
    else:
        user = request.user

    start_of_month = datetime(selected_year, selected_month, 1).date()
    if selected_month == 12:
        end_of_month = datetime(selected_year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_of_month = datetime(
            selected_year, selected_month + 1, 1
        ).date() - timedelta(days=1)

    work_logs = WorkTimeEntry.objects.filter(
        user=user, date__range=[start_of_month, end_of_month]
    ).order_by("date")

    data = []
    total_work_time = timedelta()
    total_lunch_time = timedelta()
    half_days = 0

    for log in work_logs:
        login = safe_localtime(log.login_time)
        logout = safe_localtime(log.logout_time)
        breakout = safe_localtime(log.breakout_time)
        breakin = safe_localtime(log.breakin_time)

        total_work = log.total_work_time

        if log.breakout_time and log.breakin_time:
            break_start = datetime.combine(log.date, log.breakout_time)
            break_end = datetime.combine(log.date, log.breakin_time)
            lunch_duration = break_end - break_start
        else:
            lunch_duration = timedelta()

        if total_work:
            total_work_time += total_work
            if total_work < timedelta(hours=6, minutes=30):
                half_days += 1

        total_lunch_time += lunch_duration

        data.append(
            {
                "Date": log.date.strftime("%Y-%m-%d"),
                "Login": login,
                "Logout": logout,
                "Break-Out": breakout,
                "Break-In": breakin,
                "Total-Work-Time": str(total_work or ""),
            }
        )

    df = pd.DataFrame(data)
    present_days = len(df)
    average_work_time = (
        total_work_time / present_days if present_days > 0 else timedelta()
    )

    # Convert df to HTML table
    table_html = df.to_html(index=False, classes="styled-table", border=1)

    template = get_template("worktime/worklog_pdf.html")
    html = template.render(
        {
            "user": user,
            "month": start_of_month.strftime("%B"),
            "year": selected_year,
            "table_html": table_html,
            "present_days": present_days,
            "total_work_time": total_work_time,
            "total_lunch_time": total_lunch_time,
            "average_work_time": average_work_time,
            "half_days": half_days,
        }
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="timelog_{selected_month}_{selected_year}.pdf"'
    )
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error creating PDF", status=500)
    return response


@staff_member_required
@require_POST
def update_leave_status(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)
    action = request.POST.get("action")

    if action == "approve":
        leave.status = "Approved"
    elif action == "reject":
        leave.status = "Rejected"
    leave.save()
    messages.success(request, f"Leave {action}d successfully!")
    return redirect("leaves")


@staff_member_required
@require_POST
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    action = request.POST.get("action")

    if action == "approve":
        task.status = "Approved"
    elif action == "reject":
        task.status = "Rejected"
    task.save()
    messages.success(request, f"Task {action}d successfully!")
    return redirect("task-list")
