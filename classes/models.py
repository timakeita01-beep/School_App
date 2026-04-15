from django.db import models

# Create your models here.
class Classe(models.Model):
    nom = models.CharField(max_length=30, null=False)
    niveau = models.IntegerField()