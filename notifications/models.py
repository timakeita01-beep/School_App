from django.conf import settings
from django.db import models

from classes.models import Classe
from eleves.models import Parent


class Notification(models.Model):
    """Trace d'un message envoyé par l'administration aux parents,
    soit pour une ou plusieurs classes, soit pour un parent unique."""

    message = models.TextField()
    toutes_les_classes = models.BooleanField(default=False)
    classes = models.ManyToManyField(Classe, blank=True, related_name="notifications")
    parent = models.ForeignKey(
        Parent, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="notifications",
        help_text="Renseigné uniquement pour un envoi ciblé à un seul parent.",
    )
    envoye_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    nb_destinataires = models.PositiveIntegerField(default=0)
    date_envoi = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_envoi"]

    def __str__(self):
        return f"Notification du {self.date_envoi:%d/%m/%Y %H:%M}"
