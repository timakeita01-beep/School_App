from django.db import models
from classes.models import Classe

class Matiere(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    note_sur = models.PositiveIntegerField(
        default=20,
        help_text="Barème de notation de la matière (ex: 5, 10, 20)"
    )
    coefficient = models.PositiveIntegerField(
        default=1,
        help_text="Poids de la matière dans le calcul de la moyenne"
    )
    classes = models.ManyToManyField(
        Classe,
        related_name="matieres",
        blank=True
    )

    class Meta:
        ordering = ["nom"]
        verbose_name = "Matière"
        verbose_name_plural = "Matières"

    def __str__(self):
        return f"{self.nom} (/{self.note_sur})"