from django.urls import path
from . import views

urlpatterns = [
    path("", views.bulletins_home, name="bulletins_home"),
    path("liste/", views.monthly_grades_list, name="monthly_grades_list"),
    path("eleve/<str:student_name>/<str:class_name>/<int:year>/", 
         views.bulletin_eleve, name="bulletin_eleve"),
    path("api/average/", views.student_year_average, name="student_year_average"),
]
