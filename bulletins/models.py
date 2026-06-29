from django.db import models


class MonthlyGrade(models.Model):
    """Note mensuelle (composition) pour 1ère année scolaire (Oct -> Jun).

    Pour l’instant on utilise des champs texte faute de modèles FK disponibles
    dans d’autres apps.
    """

    # À remplacer plus tard par des ForeignKey vers eleves/classes/matieres
    student_name = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255)
    subject_name = models.CharField(max_length=255)

    year = models.PositiveIntegerField(help_text="Année scolaire de référence (ex: 2024 pour 2024-2025).")

    # 1: Oct, 2: Nov, ... 6: Mar, 7: Apr, 8: May, 9: Jun (9 mois)
    month_index = models.PositiveSmallIntegerField(help_text="0=Oct puis 1=Nov ... jusqu’à 8=Jun")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student_name", "class_name", "subject_name", "year", "month_index"],
                name="unique_monthly_grade",
            )
        ]
        indexes = [
            models.Index(fields=["year", "class_name", "subject_name"]),
        ]

    def __str__(self) -> str:
        return f"{self.student_name} - {self.class_name} - {self.subject_name} ({self.year})"

    @property
    def month_label(self) -> str:
        labels = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        if 0 <= self.month_index < len(labels):
            return labels[self.month_index]
        return str(self.month_index)

