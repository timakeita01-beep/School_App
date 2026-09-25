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


class Reclamation(models.Model):
    """Signalement d'une erreur sur une note, déposé par un parent depuis le
    portail public. Circuit : le parent signale -> l'administrateur transmet
    à l'enseignant -> l'enseignant propose/valide la correction -> c'est
    l'administrateur qui l'applique effectivement (jamais l'enseignant ni
    l'administrateur seuls)."""

    NOUVELLE = "nouvelle"
    TRANSMISE = "transmise"
    VALIDEE_ENSEIGNANT = "validee_enseignant"
    REJETEE = "rejetee"
    TRAITEE = "traitee"

    STATUT_CHOICES = [
        (NOUVELLE, "Nouvelle"),
        (TRANSMISE, "Transmise à l'enseignant"),
        (VALIDEE_ENSEIGNANT, "Validée par l'enseignant"),
        (REJETEE, "Rejetée par l'enseignant"),
        (TRAITEE, "Traitée"),
    ]

    bulletin = models.ForeignKey(
        Bulletin, on_delete=models.CASCADE, related_name="reclamations"
    )

    matiere = models.ForeignKey(
        Matiere, on_delete=models.CASCADE, related_name="reclamations"
    )

    note = models.ForeignKey(
        Note, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reclamations",
        help_text="Note visée au moment du signalement (si elle existait déjà).",
    )

    message_parent = models.TextField()

    valeur_proposee = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Valeur corrigée proposée/validée par l'enseignant.",
    )

    commentaire_enseignant = models.TextField(blank=True)

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default=NOUVELLE
    )

    cree_le = models.DateTimeField(auto_now_add=True)
    maj_le = models.DateTimeField(auto_now=True)

    traitee_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reclamations_traitees",
    )

    class Meta:
        ordering = ["-cree_le"]

    def __str__(self):
        return f"Réclamation - {self.bulletin.student} - {self.matiere} ({self.get_statut_display()})"


class PromotionCampagne(models.Model):
    """Trace d'une opération de passage en classe supérieure. Rien n'est
    supprimé lors de cette opération : ce modèle conserve la liste figée des
    décisions (admis/redouble) pour l'historique et l'export."""

    annee_scolaire_cloturee = models.CharField(max_length=20)
    date_execution = models.DateTimeField(auto_now_add=True)
    realisee_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    resultats = models.JSONField(
        default=list,
        help_text="Liste figée : élève, classe d'origine, moyenne annuelle, "
                   "décision, classe de destination.",
    )

    class Meta:
        ordering = ["-date_execution"]

    def __str__(self):
        return f"Passage {self.annee_scolaire_cloturee} du {self.date_execution:%d/%m/%Y}"