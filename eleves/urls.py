from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # ── Élèves ──────────────────────────────────────────────────────────
    path('',                  views.liste_eleves,    name='liste_eleves'),
    path('<int:pk>/',         views.detail_eleve,    name='detail_eleve'),
    path('ajouter/',          views.ajouter_eleve,   name='ajouter_eleve'),
    path('<int:pk>/edit/',    views.modifier_eleve,  name='modifier_eleve'),
    path('<int:pk>/delete/',  views.supprimer_eleve, name='supprimer_eleve'),

    # ── Parents ──────────────────────────────────────────────────────────
    path('parents/',                 views.liste_parents,    name='liste_parents'),
    path('parents/ajouter/',         views.ajouter_parent,   name='ajouter_parent'),
    path('parents/<int:pk>/edit/',   views.modifier_parent,  name='modifier_parent'),
    path('parents/<int:pk>/delete/', views.supprimer_parent, name='supprimer_parent'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
