from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("admins/", views.admin_dashboard, name="admin_dashboard"),
    path("teacher/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacherlist/", views.teacher_list, name="teacher_list"),
]