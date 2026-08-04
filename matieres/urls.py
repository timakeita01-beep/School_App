from django.urls import path
from . import views

app_name = 'matieres'
urlpatterns = [
    path("matieres/", views.matiere_list, name="list"),
    path("ajouter/", views.matiere_create, name="create"),
    path("<int:pk>/", views.matiere_detail, name="detail"),
    path("<int:pk>/modifier/", views.matiere_update, name="update"),
    path("<int:pk>/supprimer/", views.matiere_delete, name="delete"),
]
 