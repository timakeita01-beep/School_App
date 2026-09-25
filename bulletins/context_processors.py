from .models import Reclamation


def reclamations_badge(request):
    """Nombre de réclamations à traiter par l'utilisateur connecté, affiché
    en badge sur l'item de navigation « Réclamations » (base.html)."""

    user = getattr(request, "user", None)

    if not user or not user.is_authenticated:
        return {}

    if user.is_staff:
        count = Reclamation.objects.filter(statut=Reclamation.NOUVELLE).count()
    elif user.groups.filter(name="Teacher").exists():
        count = Reclamation.objects.filter(
            statut=Reclamation.TRANSMISE, bulletin__classe__enseignant=user
        ).count()
    else:
        count = 0

    return {"reclamations_badge_count": count}
