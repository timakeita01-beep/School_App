from django.db import models
from classes.models import Classe

class Parent(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    profession = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Student(models.Model):
    identification_number = models.AutoField( primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    lieu_de_naissance = models.CharField(max_length=100)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='students')
    classroom = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='students')
    inscription_date = models.DateField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

