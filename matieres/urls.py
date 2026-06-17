from django.urls import path
from . import views

urlpatterns = [
    path('matieres/',views.index)
]