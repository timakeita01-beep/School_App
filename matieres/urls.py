from django.urls import path
from . import views

app_name = 'matieres'
urlpatterns = [
    path('matieres/',views.index, name='list'),
]