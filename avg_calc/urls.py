# avg_calc/urls.py

from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("timelogs/", views.work_view, name="worktime"),
    path("timelogs/edit/<int:pk>/", views.edit_timelogs, name="edit-timelogs"),
    path("timelogs/delete/<int:pk>/", views.delete_timelogs, name="delete-timelogs"),
    path("create-timelogs/", views.create_timelogs, name="create-timelogs"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("upload-timelogs/", views.upload_time_logs, name="import-timelogs"),
    path("export-template/", views.export_template, name="export-template"),
    path("expenses/", views.total_expenses, name="expenses"),
    path("create-expenses/", views.update_salary_expenses, name="create-expenses"),
    path("calculate-time/", views.calculate_work_time, name="calculate-time"),
    path("time-details/<int:pk>/", views.work_summary_detail, name="time-details"),
    path("leaves/", views.leaves, name="leaves"),
    path("apply-leave/", views.add_leave, name="apply-leave"),
    path("create-task/", views.create_task, name="create-task"),
    path("task-list/", views.task_list, name="task-list"),
    path("recent-activity/", views.recent_activity, name="recent-activity"),
    path("users/", views.users, name="user-list"),
    path("edit-user/<int:user_id>", views.edit_user, name="edit-user"),
    path("delete-user/<int:user_id>", views.delete_user, name="delete-user"),
    path("export-timelogs/pdf/", views.export_worklog, name="export-worklog"),
    path(
        "leave/<int:leave_id>/status/",
        views.update_leave_status,
        name="update-leave-status",
    ),
    path(
        "task/<int:task_id>/status/",
        views.update_task_status,
        name="update-task-status",
    ),
    path("", views.home, name="home"),
]
