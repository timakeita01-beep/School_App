from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.composer, name="composer"),
    path("<int:pk>/supprimer/", views.notification_delete, name="supprimer"),
]
