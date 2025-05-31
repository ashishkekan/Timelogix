# avg_calc/urls.py

from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("worktime/", views.work_view, name="worktime"),
    path("work/edit/<int:pk>/", views.edit_work_entry, name="edit_work_entry"),
    path("work/delete/<int:pk>/", views.delete_work_entry, name="delete_work_entry"),
    path("submit/", views.submit_work_time, name="submit_work_time"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("upload_time_logs/", views.upload_time_logs, name="upload_time_logs"),
    path("download_template/", views.download_template, name="download_template"),
    path("expenses/", views.total_expenses, name="expenses"),
    path("update-salary/", views.update_salary_expenses, name="update_salary_expenses"),
    path("calculate-work-time/", views.calculate_work_time, name="calculate_work_time"),
    path(
        "work-summary/<int:pk>/", views.work_summary_detail, name="work_summary_detail"
    ),
    path("leaves/", views.leaves, name="leaves"),
    path("apply-leave/", views.add_leave, name="apply-leave"),
    path("create_task/", views.create_task, name="create_task"),
    path("task_list/", views.task_list, name="task_list"),
    path("recent_activity/", views.recent_activity, name="recent_activity"),
]
