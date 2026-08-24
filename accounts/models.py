from django.db import models
from django.contrib.auth.models import User


class EcoleConfig(models.Model):
    """Informations de l'établissement affichées sur les bulletins
    (en-tête, signature). Modèle singleton : une seule ligne (pk=1)."""

    nom = models.CharField(max_length=150, default="Établissement scolaire")
    adresse = models.CharField(max_length=255, blank=True)
    contact = models.CharField(max_length=150, blank=True)
    nom_directeur = models.CharField(max_length=150, blank=True)
    signature_directeur = models.ImageField(
        upload_to="ecole/signatures/", blank=True, null=True,
        help_text="Signature du directeur, affichée automatiquement sur tous les bulletins."
    )

    class Meta:
        verbose_name = "Configuration de l'école"

    def __str__(self):
        return self.nom

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
