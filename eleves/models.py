from django.db import models
from classes.models import Classe

# Create your models here.
class Parent(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True, unique=True)
    telephone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nom} ({self.telephone})"


sexe_choices = [
    ('M', 'Masculin'),
    ('F', 'Feminin'),
]

statut_choices = [
    ('REGULIER', 'Régulier'),
    ('IRREGULIER', 'Irrégulier'),
]

class Eleve(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=sexe_choices)
    image = models.ImageField(upload_to='eleves/', blank=True, null=True)
    statut = models.CharField(max_length=20, choices=statut_choices)
    date_naissance = models.DateField()
    parent = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, related_name="enfants")
    classe = models.ForeignKey('classes.Classe', on_delete=models.CASCADE,related_name="eleves")
    def __str__ (self):
        return f"{self.nom} {self.prenom}"
        