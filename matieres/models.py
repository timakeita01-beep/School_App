from django.db import models

# Create your models here.
class Matiere(models.Model):
    nom = models.CharField(max_length=20, null=False)
    coef = models.IntegerField(null=False)
    classe = models.ForeignKey(
        'classes.Classe',
        on_delete=models.CASCADE,
        related_name='matieres'
    )