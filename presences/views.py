from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from bulletins.utils import lien_whatsapp
from classes.models import Classe

from .models import Presence


# ============================================================
# UTILITAIRES
# ============================================================

def est_enseignant(user):
    return user.groups.filter(name="Teacher").exists()


def est_admin(user):
    return user.is_staff


def parse_date(date_str, defaut):
    if not date_str:
        return defaut

    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return defaut


# ============================================================
# 1. FEUILLE DE PRÉSENCE (ENSEIGNANT)
# ============================================================

@login_required
def appel_classe(request, classe_id):
    """Grille Présent/Absent des élèves d'une classe pour un jour donné
    (aujourd'hui par défaut), sur le même principe que la saisie des notes."""

    classe = get_object_or_404(Classe, pk=classe_id)

    if est_enseignant(request.user) and classe.enseignant != request.user:
        messages.error(request, "Vous n'êtes pas l'enseignant de cette classe.")
        return redirect("accounts:dashboard")

    jour = parse_date(request.GET.get("date"), date.today())

    eleves = list(classe.students.all().order_by("last_name", "first_name"))

    presences_dict = {
        p.student_id: p
        for p in Presence.objects.filter(classe=classe, date=jour)
    }

    lignes = []
    for eleve in eleves:
        presence = presences_dict.get(eleve.pk)
        lignes.append({
            "eleve": eleve,
            "present": presence.present if presence else True,
            "remarque": presence.remarque if presence else "",
        })

    context = {
        "classe": classe,
        "jour": jour,
        "aujourdhui": date.today(),
        "lignes": lignes,
        "total_eleves": len(eleves),
        "appel_deja_fait": bool(presences_dict),
    }

    return render(request, "presences/appel_classe.html", context)


@login_required
def appel_bulk_save(request, classe_id):
    if request.method != "POST":
        return redirect("presences:appel_classe", classe_id=classe_id)

    classe = get_object_or_404(Classe, pk=classe_id)

    if est_enseignant(request.user) and classe.enseignant != request.user:
        messages.error(request, "Vous ne pouvez pas saisir la présence de cette classe.")
        return redirect("accounts:dashboard")

    jour = parse_date(request.POST.get("date"), date.today())
    eleves = list(classe.students.all())

    redirect_url = reverse("presences:appel_classe", args=[classe.pk]) + f"?date={jour}"

    if not eleves:
        messages.error(request, "Cette classe n'a aucun élève.")
        return redirect(redirect_url)

    for eleve in eleves:
        present = request.POST.get(f"etat_{eleve.pk}") == "present"
        remarque = request.POST.get(f"remarque_{eleve.pk}", "").strip()

        Presence.objects.update_or_create(
            student=eleve,
            date=jour,
            defaults={
                "classe": classe,
                "present": present,
                "enseignant": request.user,
                "remarque": remarque,
            },
        )

    messages.success(request, f"Appel enregistré pour {len(eleves)} élève(s) le {jour:%d/%m/%Y}.")

    return redirect(redirect_url)


# ============================================================
# 2. ALERTES D'ABSENCES (ADMIN)
# ============================================================

@login_required
def alertes_absences(request):
    if not request.user.is_staff:
        messages.error(request, "Seul l'administrateur peut consulter les alertes d'absences.")
        return redirect("accounts:dashboard")

    absences = (
        Presence.objects.filter(present=False, parent_notifie=False)
        .select_related("student", "student__parent", "classe")
    )

    historique = (
        Presence.objects.filter(present=False, parent_notifie=True)
        .select_related("student", "student__parent", "classe")[:20]
    )

    alertes = []
    for presence in absences:
        parent = presence.student.parent
        message = (
            f"Bonjour {parent.first_name}, nous vous informons que "
            f"{presence.student.first_name} {presence.student.last_name} "
            f"a été marqué(e) absent(e) le {presence.date:%d/%m/%Y}."
        )
        alertes.append({
            "presence": presence,
            "whatsapp_url": lien_whatsapp(parent.phone_number, message),
        })

    context = {
        "alertes": alertes,
        "historique": historique,
    }

    return render(request, "presences/alertes_absences.html", context)


@login_required
def marquer_notifie(request, pk):
    if not request.user.is_staff:
        messages.error(request, "Seul l'administrateur peut effectuer cette action.")
        return redirect("accounts:dashboard")

    if request.method == "POST":
        presence = get_object_or_404(Presence, pk=pk)
        presence.parent_notifie = True
        presence.save(update_fields=["parent_notifie"])
        messages.success(request, "Le parent a été marqué comme notifié.")

    return redirect("presences:alertes_absences")
