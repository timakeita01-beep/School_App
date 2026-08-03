from django.urls import path
from . import views

urlpatterns = [
    path('matieres/', views.index, name='matieres_list'),
    path('matieres/ajouter/', views.ajouter_matiere, name='matiere_ajouter'),
    path('matieres/modifier/<int:pk>/', views.modifier_matiere, name='matiere_modifier'),
    path('matieres/supprimer/<int:pk>/', views.supprimer_matiere, name='matiere_supprimer'),
]