from django.urls import path
from . import views

urlpatterns = [
    path('classes/', views.voir, name='classes_list'),
    path('classes/ajouter/', views.ajouter_classe, name='classe_ajouter'),
    path('classes/modifier/<int:pk>/', views.modifier_classe, name='classe_modifier'),
    path('classes/supprimer/<int:pk>/', views.supprimer_classe, name='classe_supprimer'),
]