from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    path('classes/', views.voir, name='list'),
    path('classes/ajouter/', views.ajouter_classe, name='ajouter'),
    path('classes/modifier/<int:pk>/', views.modifier_classe, name='modifier'),
    path('classes/supprimer/<int:pk>/', views.supprimer_classe, name='supprimer'),
    path('classes/details/<int:pk>/', views.classe_detail, name='detail'),
]