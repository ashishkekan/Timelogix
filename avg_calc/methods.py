from django.urls import reverse_lazy
from django.utils.functional import lazy

from avg_calc.models import RecentActivity
from avg_calc.templatetags.custom_filter import format_duration

safe_reverse = lambda name: lazy(lambda: str(reverse_lazy(name)), str)
safe_reverse_with_anchor = lambda name, anchor: lazy(
    lambda: str(reverse_lazy(name)) + anchor, str
)


def log_activity(user, description):
    RecentActivity.objects.create(user=user, description=description)


def get_user_stats(entries, total_work_seconds, need_time, average_time):
    return [
        {
            "title": "Total Time This Month",
            "value": (
                format_duration(total_work_seconds)
                if total_work_seconds
                else "0 hrs, 0 mins"
            ),
            "description": f"Across {entries.count()} working days",
            "icon": "fas fa-clock",
            "icon_color": "text-indigo-500",
        },
        {
            "title": "Average Time Per Day",
            "value": format_duration(need_time) if need_time else "0 hrs, 0 mins",
            "description": "Daily average calculation",
            "icon": "fas fa-chart-line",
            "icon_color": "text-teal-500",
        },
        {
            "title": "Working Days",
            "value": entries.count(),
            "description": "Excluding weekends & holidays",
            "icon": "fas fa-calendar-alt",
            "icon_color": "text-purple-500",
        },
        {
            "title": "Working Average",
            "value": format_duration(average_time) if average_time else "0 hrs, 0 mins",
            "description": "8h 40m daily target",
            "icon": "fas fa-bullseye",
            "icon_color": "text-blue-500",
        },
    ]


def get_target_status(average_time, target_seconds, need_time):
    if average_time >= target_seconds:
        return {
            "title": "Target Met",
            "message": "Great job! Your average work time meets the target of 8 hours and 40 minutes.",
            "icon": "fas fa-check-circle",
            "icon_color": "text-teal-500",
        }
    else:
        return {
            "title": "Target Not Met",
            "message": f"You need to work an additional {format_duration(need_time) if need_time else '0 hrs, 0 mins'} per day to meet the target of 8 hours and 40 minutes.",
            "icon": "fas fa-exclamation-circle",
            "icon_color": "text-red-500",
        }


def get_admin_stats(
    total_users, total_worklogs, total_expenses, total_tasks, total_leaves
):
    return [
        {
            "title": "Total Users",
            "value": total_users,
            "description": "Active employees",
            "icon": "fas fa-users",
            "icon_color": "text-indigo-600",
            "url": safe_reverse("user-list")(),
            "is_currency": False,
        },
        {
            "title": "Total TimeLogs",
            "value": total_worklogs,
            "description": "All months",
            "icon": "fas fa-clipboard-list",
            "icon_color": "text-teal-600",
            "url": safe_reverse("worktime")(),
            "is_currency": False,
        },
        {
            "title": "Total Expenses",
            "value": total_expenses,
            "description": "All period",
            "icon": "fas fa-dollar-sign",
            "icon_color": "text-purple-600",
            "url": safe_reverse("expenses")(),
            "is_currency": True,
        },
        {
            "title": "Total Tasks",
            "value": total_tasks,
            "description": "All projects",
            "icon": "fas fa-tasks",
            "icon_color": "text-blue-600",
            "url": safe_reverse("task-list")(),
            "is_currency": False,
        },
        {
            "title": "Total Leaves",
            "value": total_leaves,
            "description": "All months",
            "icon": "fas fa-leaf",
            "icon_color": "text-indigo-600",
            "url": safe_reverse("leaves")(),
            "is_currency": False,
        },
    ]


def get_quick_actions():
    return [
        {
            "url": safe_reverse("calculate-time")(),
            "title": "Calculate Work Time",
            "icon": "fas fa-calculator",
            "icon_color": "text-indigo-500",
        },
        {
            "url": safe_reverse("create-expenses")(),
            "title": "Salary Expenses",
            "icon": "fas fa-dollar-sign",
            "icon_color": "text-teal-500",
        },
        {
            "url": safe_reverse("leaves")(),
            "title": "Leaves",
            "icon": "fas fa-leaf",
            "icon_color": "text-purple-500",
        },
        {
            "url": safe_reverse("task-list")(),
            "title": "Tasks",
            "icon": "fas fa-tasks",
            "icon_color": "text-blue-500",
        },
    ]


home_context = {
    "hero": {
        "title_lines": [
            {"text": "Smart Time Tracking", "class": "block"},
            {"text": "For Productive Teams", "class": "block text-indigo-600"},
        ],
        "description": "TimeLogix helps you analyze sitting time, track tasks, calculate salary expenses, and manage leaves - all in one powerful platform.",
        "buttons": [
            {
                "text": "Start Free Trial",
                "url": safe_reverse("register")(),
                "class": "btn-primary w-full flex items-center justify-center px-8 py-3 text-base font-medium rounded-md text-white md:py-4 md:text-lg md:px-10",
            },
            {
                "text": "Live Demo",
                "url": safe_reverse("demo_login")(),
                "class": "btn-secondary w-full flex items-center justify-center px-8 py-3 text-base font-medium rounded-md text-white md:py-4 md:text-lg md:px-10",
            },
        ],
        "image": {
            "src": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            "alt": "TimeLogix dashboard preview",
            "class": "w-full dashboard-preview",
        },
    },
    "features": {
        "header": {
            "subtitle": "Features",
            "title": "Everything you need to optimize work time",
            "description": "TimeLogix combines powerful analytics with intuitive time tracking for maximum productivity.",
        },
        "items": [
            {
                "icon": "fas fa-chair",
                "title": "Sitting Time Analysis",
                "description": "Get precise estimates of your sitting time with intelligent algorithms that analyze your work patterns and suggest optimal break times.",
                "icon_bg": "bg-indigo-500",
            },
            {
                "icon": "fas fa-tasks",
                "title": "Task Time Tracking",
                "description": "Log time against specific tasks and projects with our intuitive interface. Categorize, tag, and analyze where your time goes.",
                "icon_bg": "bg-green-500",
            },
            {
                "icon": "fas fa-money-bill-wave",
                "title": "Salary & Expense Reports",
                "description": "Automatically calculate salary expenses based on logged hours and configured rates. Generate detailed reports for payroll.",
                "icon_bg": "bg-purple-500",
            },
            {
                "icon": "fas fa-calendar-alt",
                "title": "Leave Management",
                "description": "Track vacation days, sick leaves, and other time off. Get alerts for upcoming leaves and view team availability at a glance.",
                "icon_bg": "bg-blue-500",
            },
            {
                "icon": "fas fa-chart-line",
                "title": "Productivity Analytics",
                "description": "Visualize your work patterns with beautiful charts. Identify productivity trends and opportunities for improvement.",
                "icon_bg": "bg-red-500",
            },
            {
                "icon": "fas fa-bell",
                "title": "Smart Reminders",
                "description": "Get notified when you've been sitting too long, when tasks are taking longer than expected, or when important deadlines approach.",
                "icon_bg": "bg-yellow-500",
            },
        ],
    },
    "how_it_works": {
        "title": "How TimeLogix Works",
        "description": "Our simple three-step process helps you gain control over your time and productivity.",
        "steps": [
            {
                "number": "1",
                "title": "Track Your Time",
                "description": "Use our web app, desktop widget, or mobile app to track time spent on tasks. Our system automatically detects idle time.",
            },
            {
                "number": "2",
                "title": "Analyze Patterns",
                "description": "Our AI analyzes your sitting patterns, task durations, and productivity levels to provide actionable insights.",
            },
            {
                "number": "3",
                "title": "Optimize & Report",
                "description": "Use our reports to improve work habits, calculate payroll, manage leaves, and make data-driven decisions.",
            },
        ],
        "image": {
            "src": "https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80",
            "alt": "TimeLogix analytics dashboard",
            "class": "w-full dashboard-preview",
        },
    },
    "pricing": {
        "header": {
            "subtitle": "Pricing",
            "title": "Simple, transparent pricing",
            "description": "Choose the plan that fits your needs. No hidden fees, cancel anytime.",
        },
        "plans": [
            {
                "name": "Starter",
                "badge": {"text": "FREE", "class": "bg-[#14b8a6]"},
                "price": {"amount": "0", "currency": "₹", "period": "/month"},
                "description": "Perfect for individuals getting started with time tracking",
                "features": [
                    "Basic time tracking",
                    "Sitting time analysis",
                    "3 projects",
                    "Basic reports",
                ],
                "button": {
                    "text": "Get started",
                    "url": safe_reverse("register")(),
                    "class": "btn-secondary block w-full py-3 px-6 text-center rounded-md text-white font-medium",
                },
            },
            {
                "name": "Professional",
                "badge": {"text": "POPULAR", "class": "bg-[#5b21b6]"},
                "price": {"amount": "9", "currency": "₹", "period": "/month"},
                "description": "For professionals who need advanced analytics",
                "features": [
                    "Everything in Free",
                    "Unlimited projects",
                    "Advanced analytics",
                    "Salary calculations",
                    "Leave management",
                    "Priority support",
                ],
                "button": {
                    "text": "Start free trial",
                    "url": safe_reverse("register")(),
                    "class": "btn-primary block w-full py-3 px-6 text-center rounded-md text-white font-medium",
                },
                "highlight": True,
            },
            {
                "name": "Enterprise",
                "price": {"amount": "29", "currency": "₹", "period": "/month"},
                "description": "For teams and organizations needing custom solutions",
                "features": [
                    "Everything in Pro",
                    "Team management",
                    "Custom reporting",
                    "API access",
                    "Dedicated account manager",
                    "On-premise options",
                ],
                "button": {
                    "text": "Contact sales",
                    "url": safe_reverse_with_anchor("home", "#contact")(),
                    "class": "btn-secondary block w-full py-3 px-6 text-center rounded-md text-white font-medium",
                },
            },
        ],
    },
}
