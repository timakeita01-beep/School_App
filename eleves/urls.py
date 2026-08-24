from django.urls import path
from . import views

app_name = 'students'
urlpatterns = [
    path('students/', views.student_list, name='list'),
    path('students/create/', views.student_create, name='create'),
    path('students/<int:identification_number>/', views.student_detail, name='detail'),
    path('students/<int:identification_number>/update/', views.student_update, name='update'),
    path('students/<int:identification_number>/delete/', views.student_delete, name='delete'),
    path('parents/', views.parent_list, name='parent_list'),
    path('parents/create/', views.parent_create, name='parent_create'),
    path('parents/<int:parent_id>/', views.parent_detail, name='parent_detail'),
    path('parents/<int:parent_id>/update/', views.parent_update, name='parent_update'),
    path('parents/<int:parent_id>/delete/', views.parent_delete, name='parent_delete'),
]