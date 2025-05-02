"""
URL configuration for server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from avg_calc import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("admin/", admin.site.urls),
    path("worktime/", include("avg_calc.urls")),
    path("profile/", views.profile_view, name="profile"),
    path("submit/", views.submit_work_time, name="submit_work_time"),
    path("timelogs/", views.work_view, name="timelogs"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("upload_time_logs/", views.upload_time_logs, name="upload_time_logs"),
    path("download_template/", views.download_template, name="download_template"),
    path("expenses/", views.total_expenses, name="expenses"),
    path("update-salary/", views.update_salary_expenses, name="update_salary_expenses"),
    path(
        "salary-success/", views.salary_expenses_success, name="salary_expenses_success"
    ),
    path("calculate-work-time/", views.calculate_work_time, name="calculate_work_time"),
    path(
        "work-summary/<int:pk>/", views.work_summary_detail, name="work_summary_detail"
    ),
    path("leaves/", views.leaves, name="leaves"),
    path("apply-leave/", views.add_leave, name="apply-leave"),
    path("create_task/", views.create_task, name="create_task"),
    path("task_list/", views.task_list, name="task_list"),
    path("recent_activity/", views.recent_activity, name="recent_activity"),
    path("", include("django.contrib.auth.urls")),
]
