from django.urls import path
from . import views

urlpatterns = [
    path('students/', views.student_list, name='student_list'),
    path('students/<str:identification_number>/', views.student_detail, name='student_detail'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<str:identification_number>/update/', views.student_update, name='student_update'),
    path('students/<str:identification_number>/delete/', views.student_delete, name='student_delete'),
    path('parents/', views.parent_list, name='parent_list'),
    path('parents/<int:parent_id>/', views.parent_detail, name='parent_detail'),
    path('parents/create/', views.parent_create, name='parent_create'),
    path('parents/<int:parent_id>/update/', views.parent_update, name='parent_update'),
    path('parents/<int:parent_id>/delete/', views.parent_delete, name='parent_delete'),
]