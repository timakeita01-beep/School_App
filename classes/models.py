from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Classe(models.Model):
    nom = models.CharField(max_length=30, null=False)
    niveau = models.IntegerField()
    enseignant = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="classes",
        limit_choices_to={"groups__name": "Teacher"},
    )

    def __str__(self):
        return f"{self.nom}"