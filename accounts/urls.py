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
    path("teacher/create/", views.teacher_create, name="teacher_create"),
    path("teacher/<int:pk>/update/", views.teacher_update, name="teacher_update"),
    path("teacher/<int:pk>/delete/", views.teacher_delete, name="teacher_delete"),
    path("teacher/<int:pk>/profile/", views.teacher_profile, name="teacher_profile"),
]