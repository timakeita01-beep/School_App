from django.conf import settings
from django.db import models


class Presence(models.Model):
    """Présence d'un élève à une date donnée, saisie par l'enseignant de sa
    classe. Une absence (present=False) reste visible côté admin tant que
    parent_notifie=False : c'est directement le statut de l'alerte, pas
    besoin d'un modèle séparé."""

    student = models.ForeignKey(
        "eleves.Student", on_delete=models.CASCADE, related_name="presences"
    )
    classe = models.ForeignKey(
        "classes.Classe", on_delete=models.CASCADE, related_name="presences"
    )
    date = models.DateField()
    present = models.BooleanField(default=True)
    enseignant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    remarque = models.CharField(max_length=255, blank=True)
    parent_notifie = models.BooleanField(default=False)
    date_saisie = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "student__last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "date"], name="presence_unique_par_jour"
            )
        ]

    def __str__(self):
        etat = "Présent" if self.present else "Absent"
        return f"{self.student} - {self.date} - {etat}"
