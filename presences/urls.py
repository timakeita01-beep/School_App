from django.urls import path

from . import views

app_name = "presences"

urlpatterns = [
    path("classe/<int:classe_id>/", views.appel_classe, name="appel_classe"),
    path("classe/<int:classe_id>/enregistrer/", views.appel_bulk_save, name="appel_bulk_save"),

    path("alertes/", views.alertes_absences, name="alertes_absences"),
    path("alertes/<int:pk>/notifie/", views.marquer_notifie, name="marquer_notifie"),
]
