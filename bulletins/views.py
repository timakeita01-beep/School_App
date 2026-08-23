from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.models import EcoleConfig
from classes.models import Classe

from .models import Note, Bulletin
from .utils import MOIS_SCOLAIRE, ANNEE_SCOLAIRE_DEFAUT, mois_courant, mois_label


# ============================================================
# UTILITAIRES
# ============================================================

def est_enseignant(user):
    return user.groups.filter(name="Teacher").exists()


def est_admin(user):
    return user.is_staff


def classe_verrouillee(classe, mois, annee_scolaire):
    """Une classe est verrouillée pour un mois donné dès que ses bulletins
    ont été validés par l'administrateur : l'enseignant ne peut plus
    modifier les notes de cette période."""
    return Bulletin.objects.filter(
        classe=classe,
        mois=mois,
        annee_scolaire=annee_scolaire,
        valide=True,
    ).exists()


def calculer_moyenne_eleve(student, mois, annee_scolaire):
    """
    Calcule la moyenne générale de l'élève sur 10, à partir de toutes les
    matières de sa classe. Retourne None si une matière n'a pas encore de note.
    """
    classe = student.classroom
    matieres = classe.matieres.all()

    if not matieres.exists():
        return None

    total = Decimal("0")
    nombre_matieres = 0

    for matiere in matieres:
        note = Note.objects.filter(
            student=student,
            matiere=matiere,
            mois=mois,
            annee_scolaire=annee_scolaire,
        ).first()

        if note is None:
            return None

        note_sur_10 = (note.valeur * Decimal("10")) / Decimal(str(matiere.note_sur))

        total += note_sur_10
        nombre_matieres += 1

    moyenne = total / Decimal(nombre_matieres)

    return moyenne.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ============================================================
# 1. SAISIE DES NOTES (ENSEIGNANT)
# ============================================================

@login_required
def notes_classe(request, classe_id, mois):
    """
    Espace de saisie des notes d'une classe pour un mois donné :
    - sélecteur de matière (avec indicateur de complétion)
    - grille des élèves pour la matière sélectionnée
    """

    classe = get_object_or_404(Classe, pk=classe_id)

    if est_enseignant(request.user) and classe.enseignant != request.user:
        messages.error(request, "Vous n'êtes pas l'enseignant de cette classe.")
        return redirect("accounts:dashboard")

    annee_scolaire = request.GET.get("annee_scolaire", ANNEE_SCOLAIRE_DEFAUT)

    eleves = list(classe.students.all().order_by("last_name", "first_name"))
    matieres = list(classe.matieres.all())
    total_eleves = len(eleves)

    # Complétion par matière
    matieres_info = []
    matieres_completes = 0

    for matiere in matieres:
        notes_saisies = Note.objects.filter(
            matiere=matiere,
            mois=mois,
            annee_scolaire=annee_scolaire,
            student__classroom=classe,
        ).count()

        complete = total_eleves > 0 and notes_saisies == total_eleves

        if complete:
            matieres_completes += 1

        matieres_info.append({
            "matiere": matiere,
            "notes_saisies": notes_saisies,
            "complete": complete,
        })

    # Matière sélectionnée
    matiere_id = request.GET.get("matiere")
    matiere_selectionnee = None

    if matiere_id:
        matiere_selectionnee = next(
            (m["matiere"] for m in matieres_info if str(m["matiere"].pk) == str(matiere_id)),
            None,
        )

    if matiere_selectionnee is None and matieres_info:
        matiere_selectionnee = matieres_info[0]["matiere"]

    # Notes existantes pour la grille
    lignes = []

    if matiere_selectionnee:
        notes_dict = {
            note.student_id: note
            for note in Note.objects.filter(
                matiere=matiere_selectionnee,
                mois=mois,
                annee_scolaire=annee_scolaire,
                student__classroom=classe,
            )
        }

        for eleve in eleves:
            note = notes_dict.get(eleve.pk)
            lignes.append({
                "eleve": eleve,
                "valeur": note.valeur if note else "",
                "commentaire": note.commentaire if note else "",
            })

    verrouillee = classe_verrouillee(classe, mois, annee_scolaire)

    context = {
        "classe": classe,
        "mois": int(mois),
        "mois_label": mois_label(mois),
        "mois_scolaire": MOIS_SCOLAIRE,
        "annee_scolaire": annee_scolaire,
        "matieres_info": matieres_info,
        "matieres_completes": matieres_completes,
        "total_matieres": len(matieres),
        "matiere_selectionnee": matiere_selectionnee,
        "lignes": lignes,
        "total_eleves": total_eleves,
        "verrouillee": verrouillee,
    }

    return render(request, "bulletin/notes_classe.html", context)


@login_required
def notes_bulk_save(request, classe_id, mois, matiere_id):
    """
    Enregistre en une fois les notes de tous les élèves d'une classe pour
    une matière donnée. Refuse l'enregistrement si un seul élève n'a pas
    de note valide (tout ou rien).
    """

    if request.method != "POST":
        return redirect("bulletin:notes_classe", classe_id=classe_id, mois=mois)

    classe = get_object_or_404(Classe, pk=classe_id)
    matiere = get_object_or_404(classe.matieres, pk=matiere_id)

    if est_enseignant(request.user) and classe.enseignant != request.user:
        messages.error(request, "Vous ne pouvez pas saisir les notes de cette classe.")
        return redirect("accounts:dashboard")

    annee_scolaire = request.POST.get("annee_scolaire", ANNEE_SCOLAIRE_DEFAUT)

    redirect_url = (
        reverse("bulletin:notes_classe", args=[classe.pk, mois])
        + f"?matiere={matiere.pk}&annee_scolaire={annee_scolaire}"
    )

    if classe_verrouillee(classe, mois, annee_scolaire):
        messages.error(
            request,
            "Les bulletins de cette période ont déjà été validés : "
            "les notes sont verrouillées.",
        )
        return redirect(redirect_url)

    eleves = list(classe.students.all())

    if not eleves:
        messages.error(request, "Cette classe n'a aucun élève.")
        return redirect(redirect_url)

    valeurs = {}
    commentaires = {}
    erreurs = []

    for eleve in eleves:
        brut = request.POST.get(f"note_{eleve.pk}", "").strip()

        if not brut:
            erreurs.append(f"{eleve.first_name} {eleve.last_name} n'a pas de note.")
            continue

        try:
            valeur = Decimal(brut.replace(",", "."))
        except InvalidOperation:
            erreurs.append(f"La note de {eleve.first_name} {eleve.last_name} est invalide.")
            continue

        if valeur < 0 or valeur > matiere.note_sur:
            erreurs.append(
                f"La note de {eleve.first_name} {eleve.last_name} doit être "
                f"comprise entre 0 et {matiere.note_sur}."
            )
            continue

        valeurs[eleve.pk] = valeur
        commentaires[eleve.pk] = request.POST.get(f"comment_{eleve.pk}", "").strip()

    if erreurs:
        messages.error(
            request,
            "Aucune note n'a été enregistrée car la liste est incomplète : "
            + " ".join(erreurs[:5])
            + (" ..." if len(erreurs) > 5 else ""),
        )
        return redirect(redirect_url)

    with transaction.atomic():
        for eleve in eleves:
            Note.objects.update_or_create(
                student=eleve,
                matiere=matiere,
                mois=mois,
                annee_scolaire=annee_scolaire,
                defaults={
                    "enseignant": request.user,
                    "valeur": valeurs[eleve.pk],
                    "commentaire": commentaires[eleve.pk],
                },
            )

    messages.success(
        request,
        f"Notes de « {matiere.nom} » enregistrées pour {len(eleves)} élève(s).",
    )

    return redirect(redirect_url)


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk)
    classe = note.student.classroom

    if est_enseignant(request.user) and classe.enseignant != request.user:
        messages.error(request, "Vous ne pouvez pas supprimer cette note.")
        return redirect("accounts:dashboard")

    if classe_verrouillee(classe, note.mois, note.annee_scolaire):
        messages.error(
            request,
            "Les bulletins de cette période ont déjà été validés : "
            "les notes sont verrouillées.",
        )
        return redirect("bulletin:notes_classe", classe_id=classe.pk, mois=note.mois)

    classe_id = classe.pk
    mois = note.mois
    matiere_id = note.matiere_id

    note.delete()

    messages.success(request, "La note a été supprimée.")

    return redirect(
        reverse("bulletin:notes_classe", args=[classe_id, mois]) + f"?matiere={matiere_id}"
    )


# ============================================================
# 2. ESPACE ADMIN : CLASSES / VALIDATION / NOTIFICATION
# ============================================================

@login_required
def bulletin_list(request):
    """Accueil bulletins (admin) : les classes en cartes, avec le statut de
    saisie des notes et la validation des bulletins pour le mois choisi."""

    if not est_admin(request.user):
        messages.error(request, "Seul l'administrateur peut accéder à cette page.")
        return redirect("accounts:dashboard")

    mois = int(request.GET.get("mois", mois_courant()))
    annee_scolaire = request.GET.get("annee_scolaire", ANNEE_SCOLAIRE_DEFAUT)

    classes_info = []

    for classe in Classe.objects.all().order_by("-niveau", "nom"):
        eleves = list(classe.students.all().order_by("last_name", "first_name"))
        total_eleves = len(eleves)

        valide = classe_verrouillee(classe, mois, annee_scolaire)

        eleves_rows = []
        eleves_complets = 0

        bulletins_par_eleve = {}

        if valide:
            bulletins = Bulletin.objects.filter(
                classe=classe, mois=mois, annee_scolaire=annee_scolaire
            ).select_related("student").order_by("rang")

            bulletins_par_eleve = {b.student_id: b for b in bulletins}

            for eleve in eleves:
                bulletin = bulletins_par_eleve.get(eleve.pk)
                eleves_rows.append({"eleve": eleve, "bulletin": bulletin})
                if bulletin:
                    eleves_complets += 1
        else:
            for eleve in eleves:
                moyenne = calculer_moyenne_eleve(eleve, mois, annee_scolaire)
                complet = moyenne is not None
                if complet:
                    eleves_complets += 1
                eleves_rows.append({"eleve": eleve, "moyenne": moyenne, "complet": complet})

        classes_info.append({
            "classe": classe,
            "total_eleves": total_eleves,
            "eleves_complets": eleves_complets,
            "eleves_rows": eleves_rows,
            "valide": valide,
            "prete_a_valider": total_eleves > 0 and eleves_complets == total_eleves and not valide,
        })

    context = {
        "classes_info": classes_info,
        "mois": mois,
        "mois_label": mois_label(mois),
        "mois_scolaire": MOIS_SCOLAIRE,
        "annee_scolaire": annee_scolaire,
    }

    return render(request, "bulletin/bulletins.html", context)


@login_required
def valider_classe(request, classe_id):
    """Calcule les moyennes/rangs et valide d'un coup les bulletins d'une
    classe pour le mois choisi. Verrouille ensuite la saisie des notes."""

    if not est_admin(request.user):
        messages.error(request, "Seul l'administrateur peut valider les bulletins.")
        return redirect("accounts:dashboard")

    if request.method != "POST":
        return redirect("bulletin:liste")

    classe = get_object_or_404(Classe, pk=classe_id)
    mois = int(request.POST.get("mois"))
    annee_scolaire = request.POST.get("annee_scolaire", ANNEE_SCOLAIRE_DEFAUT)

    redirect_url = (
        reverse("bulletin:liste") + f"?mois={mois}&annee_scolaire={annee_scolaire}"
    )

    eleves = classe.students.all()
    resultats = []

    for eleve in eleves:
        moyenne = calculer_moyenne_eleve(eleve, mois, annee_scolaire)
        if moyenne is not None:
            resultats.append({"student": eleve, "moyenne": moyenne})

    if not resultats:
        messages.error(
            request,
            "Aucun bulletin ne peut être validé : vérifiez que toutes les "
            "notes de la classe sont saisies pour ce mois.",
        )
        return redirect(redirect_url)

    resultats.sort(key=lambda x: x["moyenne"], reverse=True)

    with transaction.atomic():
        for index, resultat in enumerate(resultats):
            Bulletin.objects.update_or_create(
                student=resultat["student"],
                mois=mois,
                annee_scolaire=annee_scolaire,
                defaults={
                    "classe": classe,
                    "moyenne_generale": resultat["moyenne"],
                    "rang": index + 1,
                    "valide": True,
                },
            )

    messages.success(
        request,
        f"Les bulletins de « {classe.nom} » ont été calculés et validés "
        f"pour {len(resultats)} élève(s).",
    )

    return redirect(redirect_url)


@login_required
def notifier_parents(request, classe_id):
    """Envoie le bulletin de chaque élève par e-mail à son parent."""

    if not est_admin(request.user):
        messages.error(request, "Seul l'administrateur peut notifier les parents.")
        return redirect("accounts:dashboard")

    if request.method != "POST":
        return redirect("bulletin:liste")

    classe = get_object_or_404(Classe, pk=classe_id)
    mois = int(request.POST.get("mois"))
    annee_scolaire = request.POST.get("annee_scolaire", ANNEE_SCOLAIRE_DEFAUT)

    redirect_url = (
        reverse("bulletin:liste") + f"?mois={mois}&annee_scolaire={annee_scolaire}"
    )

    bulletins = Bulletin.objects.filter(
        classe=classe, mois=mois, annee_scolaire=annee_scolaire, valide=True
    ).select_related("student", "student__parent")

    if not bulletins.exists():
        messages.error(
            request,
            "Les bulletins de cette classe doivent d'abord être validés.",
        )
        return redirect(redirect_url)

    envoyes = 0
    sans_email = 0

    for bulletin in bulletins:
        parent = bulletin.student.parent
        email = parent.email if parent else None

        if not email:
            sans_email += 1
            continue

        lien = request.build_absolute_uri(
            reverse("bulletin:detail", args=[bulletin.pk])
        )

        send_mail(
            subject=f"Bulletin de {bulletin.student.first_name} {bulletin.student.last_name} "
                    f"- {mois_label(mois)} {annee_scolaire}",
            message=(
                f"Bonjour {parent.first_name},\n\n"
                f"Le bulletin de {bulletin.student.first_name} {bulletin.student.last_name} "
                f"({classe.nom}) pour {mois_label(mois)} {annee_scolaire} est disponible.\n"
                f"Moyenne générale : {bulletin.moyenne_generale}/10 — Rang : {bulletin.rang}\n\n"
                f"Consultez-le ici : {lien}\n"
            ),
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
        )
        envoyes += 1

    if envoyes:
        messages.success(request, f"{envoyes} bulletin(s) notifié(s) par e-mail aux parents.")
    if sans_email:
        messages.warning(
            request,
            f"{sans_email} élève(s) n'ont pas pu être notifiés (aucun e-mail parent renseigné).",
        )

    return redirect(redirect_url)


@login_required
def bulletin_detail(request, pk):
    bulletin = get_object_or_404(
        Bulletin.objects.select_related("student", "classe"), pk=pk
    )

    if est_enseignant(request.user) and bulletin.classe.enseignant != request.user:
        messages.error(request, "Vous n'avez pas accès à ce bulletin.")
        return redirect("accounts:dashboard")

    matieres = bulletin.classe.matieres.all()

    notes = Note.objects.filter(
        student=bulletin.student,
        mois=bulletin.mois,
        annee_scolaire=bulletin.annee_scolaire,
    ).select_related("matiere")

    notes_dict = {note.matiere_id: note for note in notes}

    lignes = []

    for matiere in matieres:
        note = notes_dict.get(matiere.id)
        note_sur_10 = None

        if note:
            note_sur_10 = (
                (note.valeur * Decimal("10")) / Decimal(str(matiere.note_sur))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        moyenne_classe_brute = Note.objects.filter(
            matiere=matiere,
            mois=bulletin.mois,
            annee_scolaire=bulletin.annee_scolaire,
            student__classroom=bulletin.classe,
        ).aggregate(moyenne=Avg("valeur"))["moyenne"]

        moyenne_classe_sur_10 = None

        if moyenne_classe_brute is not None:
            moyenne_classe_sur_10 = (
                (Decimal(str(moyenne_classe_brute)) * Decimal("10")) / Decimal(str(matiere.note_sur))
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        lignes.append({
            "matiere": matiere,
            "note": note,
            "note_sur_10": note_sur_10,
            "moyenne_classe": moyenne_classe_sur_10,
        })

    context = {
        "bulletin": bulletin,
        "eleve": bulletin.student,
        "classe": bulletin.classe,
        "mois_label": mois_label(bulletin.mois),
        "lignes": lignes,
        "effectif_classe": bulletin.classe.students.count(),
        "ecole": EcoleConfig.get_solo(),
    }

    return render(request, "bulletin/bulletin_detail.html", context)
