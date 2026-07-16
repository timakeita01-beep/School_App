from django import forms
from .models import Parent, Student

class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'profession']

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'date_of_birth', 'lieu_de_naissance', 'parent', 'classroom', 'inscription_date']