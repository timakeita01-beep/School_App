from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("admin/", views.admin_dashboard, name="admin_dashboard"),
    path("teacher/", views.teacher_dashboard, name="teacher_dashboard"),
]