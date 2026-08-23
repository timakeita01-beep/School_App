from django.db import models
from django.contrib.auth.models import User
from eleves.models import Student
from matieres.models import Matiere

class Note(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="notes"
    )

    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name="notes"
    )

    enseignant = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes_saisies"
    )

    mois = models.PositiveIntegerField()

    annee_scolaire = models.CharField(
        max_length=20,
        default="2026-2027"
    )

    valeur = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    commentaire = models.TextField(
        blank=True,
        null=True
    )

    date_saisie = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["matiere__nom"]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "matiere",
                    "mois",
                    "annee_scolaire"
                ],
                name="note_unique_par_mois"
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.matiere} - {self.valeur}"


class Bulletin(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="bulletins"
    )

    classe = models.ForeignKey(
        "classes.Classe",
        on_delete=models.CASCADE,
        related_name="bulletins"
    )

    mois = models.PositiveIntegerField()

    annee_scolaire = models.CharField(
        max_length=20,
        default="2026-2027"
    )

    moyenne_generale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    rang = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    avis_conseil = models.TextField(
        blank=True,
        null=True
    )

    valide = models.BooleanField(
        default=False
    )

    date_creation = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "student",
                    "mois",
                    "annee_scolaire"
                ],
                name="bulletin_unique_par_mois"
            )
        ]

    def __str__(self):
        return f"Bulletin - {self.student} - {self.mois}/{self.annee_scolaire}"