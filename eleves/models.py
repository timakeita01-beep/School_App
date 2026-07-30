from django.db import models
from classes.models import Classe

class Parent(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=110, blank=False, null=False)
    last_name = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=False, null=False)
    address = models.TextField(blank=False, null=False)
    profession = models.CharField(max_length=100, blank=False, null=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Student(models.Model):
    identification_number = models.AutoField( primary_key=True)
    first_name = models.CharField(max_length=100, blank=False, null=False)
    last_name = models.CharField(max_length=100, blank=False, null=False)
    date_of_birth = models.DateField()
    lieu_de_naissance = models.CharField(max_length=100, blank=False, null=False)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='students')
    classroom = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='students')
    inscription_date = models.DateField(blank=False, null=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age_display(self):      
        from datetime import date
        today = date.today()
        age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return f"{age} ans"