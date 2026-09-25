import csv
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage, send_mail
from django.db import transaction
from django.db.models import Avg
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.models import EcoleConfig
from classes.models import Classe
from eleves.models import Parent
from matieres.models import Matiere

from .models import Note, Bulletin, Reclamation, PromotionCampagne
from .pdf import generer_bulletin_pdf, nom_fichier_pdf
from .utils import (
    MOIS_SCOLAIRE, mois_courant, mois_label, lien_whatsapp,
    annee_active, annees_disponibles, annee_suivante,
)


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

    annee_scolaire = request.GET.get("annee_scolaire", annee_active())

    eleves = list(classe.students.filter(actif=True).order_by("last_name", "first_name"))
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

    annee_scolaire = request.POST.get("annee_scolaire", annee_active())

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

    eleves = list(classe.students.filter(actif=True))

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
    annee_scolaire = request.GET.get("annee_scolaire", annee_active())

    classes_info = []

    for classe in Classe.objects.all().order_by("-niveau", "nom"):
        eleves = list(classe.students.filter(actif=True).order_by("last_name", "first_name"))
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
                whatsapp_url = None

                if bulletin and eleve.parent:
                    lien = request.build_absolute_uri(
                        reverse(
                            "bulletin:bulletin_public",
                            args=[eleve.parent.portal_token, bulletin.pk],
                        )
                    )
                    message = (
                        f"Bonjour, le bulletin de {eleve.first_name} {eleve.last_name} "
                        f"({mois_label(mois)} {annee_scolaire}) est disponible. "
                        f"Vous pouvez le télécharger ici : {lien}"
                    )
                    whatsapp_url = lien_whatsapp(eleve.parent.phone_number, message)

                eleves_rows.append({
                    "eleve": eleve,
                    "bulletin": bulletin,
                    "whatsapp_url": whatsapp_url,
                })
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
        "annees_disponibles": annees_disponibles(),
    }

    return render(request, "bulletin/bulletins.html", context)


def _recalculer_et_valider_classe(classe, mois, annee_scolaire):
    """Calcule les moyennes/rangs de toute la classe pour ce mois et
    (re)valide les bulletins correspondants. Réutilisé par la validation
    admin classique et par l'application d'une correction de note suite à
    réclamation (le recalcul doit impacter le classement de toute la
    classe, pas seulement l'élève concerné)."""

    eleves = classe.students.filter(actif=True)
    resultats = []

    for eleve in eleves:
        moyenne = calculer_moyenne_eleve(eleve, mois, annee_scolaire)
        if moyenne is not None:
            resultats.append({"student": eleve, "moyenne": moyenne})

    if not resultats:
        return resultats

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

    return resultats


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
    annee_scolaire = request.POST.get("annee_scolaire", annee_active())

    redirect_url = (
        reverse("bulletin:liste") + f"?mois={mois}&annee_scolaire={annee_scolaire}"
    )

    resultats = _recalculer_et_valider_classe(classe, mois, annee_scolaire)

    if not resultats:
        messages.error(
            request,
            "Aucun bulletin ne peut être validé : vérifiez que toutes les "
            "notes de la classe sont saisies pour ce mois.",
        )
        return redirect(redirect_url)

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
    annee_scolaire = request.POST.get("annee_scolaire", annee_active())

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
    echecs_pdf = 0

    for bulletin in bulletins:
        parent = bulletin.student.parent
        email = parent.email if parent else None

        if not email:
            sans_email += 1
            continue

        pdf_bytes = generer_bulletin_pdf(_contexte_bulletin(bulletin))

        if pdf_bytes is None:
            echecs_pdf += 1
            continue

        message = EmailMessage(
            subject=f"Bulletin de {bulletin.student.first_name} {bulletin.student.last_name} "
                    f"- {mois_label(mois)} {annee_scolaire}",
            body=(
                f"Bonjour {parent.first_name},\n\n"
                f"Veuillez trouver ci-joint le bulletin de {bulletin.student.first_name} "
                f"{bulletin.student.last_name} ({classe.nom}) pour {mois_label(mois)} {annee_scolaire}.\n"
                f"Moyenne générale : {bulletin.moyenne_generale}/10 — Rang : {bulletin.rang}\n"
            ),
            from_email=None,
            to=[email],
        )
        message.attach(nom_fichier_pdf(bulletin), pdf_bytes, "application/pdf")
        message.send(fail_silently=True)
        envoyes += 1

    if envoyes:
        messages.success(request, f"{envoyes} bulletin(s) envoyé(s) en PDF par e-mail aux parents.")
    if echecs_pdf:
        messages.warning(
            request,
            f"{echecs_pdf} bulletin(s) n'ont pas pu être envoyés (échec de génération du PDF).",
        )
    if sans_email:
        messages.warning(
            request,
            f"{sans_email} élève(s) n'ont pas pu être notifiés (aucun e-mail parent renseigné).",
        )

    return redirect(redirect_url)


def _contexte_bulletin(bulletin):
    """Construit le contexte d'affichage d'un bulletin (utilisé par la vue
    admin/enseignant connectée et par le portail parent public)."""

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

    return {
        "bulletin": bulletin,
        "eleve": bulletin.student,
        "classe": bulletin.classe,
        "mois_label": mois_label(bulletin.mois),
        "lignes": lignes,
        "effectif_classe": bulletin.classe.students.count(),
        "ecole": EcoleConfig.get_solo(),
    }


@login_required
def bulletin_detail(request, pk):
    bulletin = get_object_or_404(
        Bulletin.objects.select_related("student", "classe"), pk=pk
    )

    if est_enseignant(request.user) and bulletin.classe.enseignant != request.user:
        messages.error(request, "Vous n'avez pas accès à ce bulletin.")
        return redirect("accounts:dashboard")

    return render(request, "bulletin/bulletin_detail.html", _contexte_bulletin(bulletin))


@login_required
def bulletin_pdf(request, pk):
    """Téléchargement du PDF du bulletin, réservé à l'admin et à
    l'enseignant de la classe (même accès que bulletin_detail)."""

    bulletin = get_object_or_404(
        Bulletin.objects.select_related("student", "classe"), pk=pk
    )

    if est_enseignant(request.user) and bulletin.classe.enseignant != request.user:
        messages.error(request, "Vous n'avez pas accès à ce bulletin.")
        return redirect("accounts:dashboard")

    pdf_bytes = generer_bulletin_pdf(_contexte_bulletin(bulletin))

    if pdf_bytes is None:
        messages.error(request, "La génération du PDF a échoué. Réessayez.")
        return redirect("bulletin:detail", pk=bulletin.pk)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{nom_fichier_pdf(bulletin)}"'
    return response


# ============================================================
# 3. PORTAIL PARENT (accès public, sans connexion, via jeton)
# ============================================================

def portail_parent(request, token):
    """Page publique (aucune connexion requise) : un parent accède, via son
    lien personnel (WhatsApp/e-mail), à la liste des bulletins validés de
    tous ses enfants."""

    parent = get_object_or_404(Parent, portal_token=token)

    enfants = parent.students.select_related("classroom").order_by("first_name")

    fiches = []

    for enfant in enfants:
        bulletins = Bulletin.objects.filter(
            student=enfant, valide=True
        ).order_by("-annee_scolaire", "-mois")

        fiches.append({
            "eleve": enfant,
            "bulletins": [
                {"bulletin": b, "mois_label": mois_label(b.mois)} for b in bulletins
            ],
        })

    context = {
        "parent": parent,
        "fiches": fiches,
        "ecole": EcoleConfig.get_solo(),
    }

    return render(request, "bulletin/portail_parent.html", context)


def bulletin_public(request, token, pk):
    """Version imprimable d'un bulletin, accessible sans connexion au parent
    concerné (le jeton doit correspondre au parent de l'élève du bulletin)."""

    bulletin = get_object_or_404(
        Bulletin.objects.select_related("student", "classe"), pk=pk, valide=True
    )

    parent = get_object_or_404(Parent, portal_token=token)

    if bulletin.student.parent_id != parent.pk:
        messages.error(request, "Ce lien ne donne pas accès à ce bulletin.")
        return redirect("bulletin:portail_parent", token=token)

    context = _contexte_bulletin(bulletin)
    context["token"] = token

    return render(request, "bulletin/bulletin_public.html", context)


def bulletin_pdf_public(request, token, pk):
    """Téléchargement du PDF par le parent, sans connexion (même contrôle
    d'accès par jeton que bulletin_public)."""

    bulletin = get_object_or_404(
        Bulletin.objects.select_related("student", "classe"), pk=pk, valide=True
    )

    parent = get_object_or_404(Parent, portal_token=token)

    if bulletin.student.parent_id != parent.pk:
        messages.error(request, "Ce lien ne donne pas accès à ce bulletin.")
        return redirect("bulletin:portail_parent", token=token)

    pdf_bytes = generer_bulletin_pdf(_contexte_bulletin(bulletin))

    if pdf_bytes is None:
        messages.error(request, "La génération du PDF a échoué. Réessayez.")
        return redirect("bulletin:bulletin_public", token=token, pk=bulletin.pk)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{nom_fichier_pdf(bulletin)}"'
    return response


# ============================================================
# 4. RÉCLAMATIONS SUR LES NOTES
# ============================================================

def reclamation_creer(request, token, pk, matiere_id):
    """Point d'entrée public (portail parent, sans connexion) : le parent
    signale une erreur sur la note d'une matière d'un bulletin validé."""

    bulletin = get_object_or_404(
        Bulletin.objects.select_related("student", "classe"), pk=pk, valide=True
    )
    parent = get_object_or_404(Parent, portal_token=token)

    if bulletin.student.parent_id != parent.pk:
        messages.error(request, "Ce lien ne donne pas accès à ce bulletin.")
        return redirect("bulletin:portail_parent", token=token)

    matiere = get_object_or_404(Matiere, pk=matiere_id)

    if request.method == "POST":
        message = request.POST.get("message", "").strip()

        if not message:
            messages.error(request, "Merci de décrire le problème rencontré.")
            return redirect("bulletin:bulletin_public", token=token, pk=bulletin.pk)

        note = Note.objects.filter(
            student=bulletin.student,
            matiere=matiere,
            mois=bulletin.mois,
            annee_scolaire=bulletin.annee_scolaire,
        ).first()

        Reclamation.objects.create(
            bulletin=bulletin,
            matiere=matiere,
            note=note,
            message_parent=message,
        )

        messages.success(
            request,
            "Votre signalement a bien été envoyé à l'administration. "
            "Nous reviendrons vers vous après vérification.",
        )

    return redirect("bulletin:bulletin_public", token=token, pk=bulletin.pk)


@login_required
def reclamations_liste(request):
    """Espace admin : réclamations à transmettre à l'enseignant, en attente
    de saisie de la correction, ou déjà traitées/rejetées."""

    if not est_admin(request.user):
        messages.error(request, "Seul l'administrateur peut accéder à cette page.")
        return redirect("accounts:dashboard")

    nouvelles = Reclamation.objects.filter(
        statut=Reclamation.NOUVELLE
    ).select_related("bulletin__student", "bulletin__classe", "matiere", "note")

    en_attente_saisie = Reclamation.objects.filter(
        statut=Reclamation.VALIDEE_ENSEIGNANT
    ).select_related("bulletin__student", "bulletin__classe", "matiere", "note")

    transmises = Reclamation.objects.filter(
        statut=Reclamation.TRANSMISE
    ).select_related("bulletin__student", "bulletin__classe", "matiere")

    historique = Reclamation.objects.filter(
        statut__in=[Reclamation.TRAITEE, Reclamation.REJETEE]
    ).select_related(
        "bulletin__student", "bulletin__classe", "matiere", "traitee_par"
    )[:30]

    context = {
        "nouvelles": nouvelles,
        "en_attente_saisie": en_attente_saisie,
        "transmises": transmises,
        "historique": historique,
    }

    return render(request, "bulletin/reclamations.html", context)


@login_required
def reclamation_transmettre(request, pk):
    if not est_admin(request.user):
        messages.error(request, "Seul l'administrateur peut effectuer cette action.")
        return redirect("accounts:dashboard")

    if request.method == "POST":
        reclamation = get_object_or_404(
            Reclamation.objects.select_related("bulletin__classe"),
            pk=pk, statut=Reclamation.NOUVELLE,
        )
        enseignant = reclamation.bulletin.classe.enseignant
        reclamation.statut = Reclamation.TRANSMISE
        reclamation.save(update_fields=["statut", "maj_le"])

        nom_enseignant = (enseignant.get_full_name() if enseignant else "") or "l'enseignant de la classe"
        messages.success(
            request,
            f"La réclamation a été transmise à {nom_enseignant}.",
        )

    return redirect("bulletin:reclamations")


@login_required
def reclamation_appliquer(request, pk):
    """L'administrateur applique la valeur proposée/validée par
    l'enseignant : écrit la note corrigée, relance le calcul moyenne/rang
    de toute la classe, et peut renotifier le parent."""

    if not est_admin(request.user):
        messages.error(request, "Seul l'administrateur peut effectuer cette action.")
        return redirect("accounts:dashboard")

    if request.method != "POST":
        return redirect("bulletin:reclamations")

    reclamation = get_object_or_404(
        Reclamation.objects.select_related("bulletin__student", "bulletin__classe", "matiere"),
        pk=pk, statut=Reclamation.VALIDEE_ENSEIGNANT,
    )

    if reclamation.valeur_proposee is None:
        messages.error(request, "Aucune valeur proposée par l'enseignant pour cette réclamation.")
        return redirect("bulletin:reclamations")

    bulletin = reclamation.bulletin
    eleve = bulletin.student
    classe = bulletin.classe
    matiere = reclamation.matiere

    if reclamation.valeur_proposee < 0 or reclamation.valeur_proposee > matiere.note_sur:
        messages.error(
            request,
            f"La valeur proposée ({reclamation.valeur_proposee}) est hors barème "
            f"(0 à {matiere.note_sur}).",
        )
        return redirect("bulletin:reclamations")

    Note.objects.update_or_create(
        student=eleve,
        matiere=matiere,
        mois=bulletin.mois,
        annee_scolaire=bulletin.annee_scolaire,
        defaults={
            "enseignant": classe.enseignant,
            "valeur": reclamation.valeur_proposee,
            "commentaire": reclamation.commentaire_enseignant,
        },
    )

    _recalculer_et_valider_classe(classe, bulletin.mois, bulletin.annee_scolaire)

    reclamation.statut = Reclamation.TRAITEE
    reclamation.traitee_par = request.user
    reclamation.save(update_fields=["statut", "traitee_par", "maj_le"])

    messages.success(
        request,
        f"La note de {eleve.first_name} {eleve.last_name} en {matiere.nom} a été corrigée "
        "et le bulletin recalculé.",
    )

    if request.POST.get("renotifier_parent") == "on":
        parent = eleve.parent
        bulletin_maj = Bulletin.objects.get(
            student=eleve, mois=bulletin.mois, annee_scolaire=bulletin.annee_scolaire
        )

        if parent and parent.email:
            pdf_bytes = generer_bulletin_pdf(_contexte_bulletin(bulletin_maj))

            if pdf_bytes is None:
                messages.warning(request, "Impossible de notifier le parent : échec de génération du PDF.")
            else:
                message = EmailMessage(
                    subject=(
                        f"Bulletin corrigé de {eleve.first_name} {eleve.last_name} - "
                        f"{mois_label(bulletin.mois)} {bulletin.annee_scolaire}"
                    ),
                    body=(
                        f"Bonjour {parent.first_name},\n\n"
                        f"Suite à votre signalement, la note de {matiere.nom} a été corrigée. "
                        f"Veuillez trouver ci-joint le bulletin mis à jour de "
                        f"{eleve.first_name} {eleve.last_name}.\n"
                    ),
                    from_email=None,
                    to=[parent.email],
                )
                message.attach(nom_fichier_pdf(bulletin_maj), pdf_bytes, "application/pdf")
                message.send(fail_silently=True)
                messages.success(request, "Le parent a été notifié par e-mail avec le bulletin en PDF.")
        else:
            messages.warning(request, "Impossible de notifier le parent : aucun e-mail renseigné.")

    return redirect("bulletin:reclamations")


@login_required
def reclamations_enseignant(request):
    """Espace enseignant : réclamations transmises par l'administration sur
    ses classes, à valider (proposer une correction) ou rejeter."""

    if not est_enseignant(request.user):
        messages.error(request, "Cette page est réservée aux enseignants.")
        return redirect("accounts:dashboard")

    reclamations = Reclamation.objects.filter(
        statut=Reclamation.TRANSMISE, bulletin__classe__enseignant=request.user,
    ).select_related("bulletin__student", "bulletin__classe", "matiere", "note")

    historique = Reclamation.objects.filter(
        statut__in=[Reclamation.VALIDEE_ENSEIGNANT, Reclamation.REJETEE, Reclamation.TRAITEE],
        bulletin__classe__enseignant=request.user,
    ).select_related("bulletin__student", "bulletin__classe", "matiere")[:20]

    context = {"reclamations": reclamations, "historique": historique}

    return render(request, "bulletin/reclamations_enseignant.html", context)


@login_required
def reclamation_valider(request, pk):
    if not est_enseignant(request.user):
        messages.error(request, "Cette page est réservée aux enseignants.")
        return redirect("accounts:dashboard")

    if request.method != "POST":
        return redirect("bulletin:reclamations_enseignant")

    reclamation = get_object_or_404(
        Reclamation, pk=pk, statut=Reclamation.TRANSMISE,
        bulletin__classe__enseignant=request.user,
    )

    brut = request.POST.get("valeur_proposee", "").strip()
    commentaire = request.POST.get("commentaire", "").strip()

    try:
        valeur = Decimal(brut.replace(",", "."))
    except InvalidOperation:
        messages.error(request, "Merci de renseigner une valeur de note valide.")
        return redirect("bulletin:reclamations_enseignant")

    matiere = reclamation.matiere

    if valeur < 0 or valeur > matiere.note_sur:
        messages.error(request, f"La note doit être comprise entre 0 et {matiere.note_sur}.")
        return redirect("bulletin:reclamations_enseignant")

    reclamation.valeur_proposee = valeur
    reclamation.commentaire_enseignant = commentaire
    reclamation.statut = Reclamation.VALIDEE_ENSEIGNANT
    reclamation.save(update_fields=["valeur_proposee", "commentaire_enseignant", "statut", "maj_le"])

    messages.success(
        request,
        "La correction a été validée et transmise à l'administration pour application.",
    )

    return redirect("bulletin:reclamations_enseignant")


@login_required
def reclamation_rejeter(request, pk):
    if not est_enseignant(request.user):
        messages.error(request, "Cette page est réservée aux enseignants.")
        return redirect("accounts:dashboard")

    if request.method != "POST":
        return redirect("bulletin:reclamations_enseignant")

    reclamation = get_object_or_404(
        Reclamation, pk=pk, statut=Reclamation.TRANSMISE,
        bulletin__classe__enseignant=request.user,
    )

    commentaire = request.POST.get("commentaire", "").strip()

    if not commentaire:
        messages.error(request, "Merci d'indiquer un motif de rejet.")
        return redirect("bulletin:reclamations_enseignant")

    reclamation.commentaire_enseignant = commentaire
    reclamation.statut = Reclamation.REJETEE
    reclamation.save(update_fields=["commentaire_enseignant", "statut", "maj_le"])

    messages.success(request, "La réclamation a été rejetée.")

    return redirect("bulletin:reclamations_enseignant")


# ============================================================
# 5. PASSAGE EN CLASSE SUPÉRIEURE (FIN D'ANNÉE)
# ============================================================

# Mois pris en compte pour la moyenne annuelle : Octobre à Juin (9 mois).
# Septembre est exclu (les cours démarrent réellement en octobre). Un mois
# sans bulletin validé compte pour 0 : ça pénalise l'élève plutôt que de
# bloquer le calcul.
MOIS_PROMOTION = [10, 11, 12, 1, 2, 3, 4, 5, 6]
SEUIL_PASSAGE = Decimal("5")


def _moyenne_annuelle(student, annee_scolaire):
    total = Decimal("0")

    for mois in MOIS_PROMOTION:
        bulletin = Bulletin.objects.filter(
            student=student, mois=mois, annee_scolaire=annee_scolaire, valide=True
        ).first()
        total += bulletin.moyenne_generale if bulletin else Decimal("0")

    return (total / Decimal(len(MOIS_PROMOTION))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def _classe_superieure(classe):
    """Classe du niveau directement supérieur, créée automatiquement si
    elle n'existe pas encore (en pratique les 6 niveaux existent déjà)."""

    niveau_suivant = classe.niveau + 1
    nom = "1ère Année" if niveau_suivant == 1 else f"{niveau_suivant}ème Année"
    classe_sup, _ = Classe.objects.get_or_create(
        niveau=niveau_suivant, defaults={"nom": nom}
    )
    return classe_sup


def _classes_avec_moyennes(annee_scolaire):
    classes_info = []

    for classe in Classe.objects.all().order_by("niveau", "nom"):
        eleves = classe.students.filter(actif=True).order_by("last_name", "first_name")
        lignes = []

        for eleve in eleves:
            moyenne = _moyenne_annuelle(eleve, annee_scolaire)
            lignes.append({
                "eleve": eleve,
                "moyenne": moyenne,
                "admis": moyenne >= SEUIL_PASSAGE,
            })

        classes_info.append({"classe": classe, "lignes": lignes})

    return classes_info


@login_required
def passage_annee(request):
    """Fin d'année : calcule la moyenne annuelle de chaque élève actif,
    propose une liste admis/redouble éditable, puis applique les décisions
    (transfert de classe ou sortie pour la 6ème année) sans jamais rien
    supprimer."""

    if not est_admin(request.user):
        messages.error(
            request,
            "Seul l'administrateur peut effectuer le passage en classe supérieure.",
        )
        return redirect("accounts:dashboard")

    annee_scolaire = (
        request.POST.get("annee_scolaire")
        or request.GET.get("annee_scolaire")
        or annee_active()
    )

    classes_info = _classes_avec_moyennes(annee_scolaire)

    if request.method == "POST":
        resultats = []

        with transaction.atomic():
            for info in classes_info:
                classe = info["classe"]

                for ligne in info["lignes"]:
                    eleve = ligne["eleve"]
                    admis_final = request.POST.get(f"admis_{eleve.pk}") == "on"

                    if admis_final and classe.niveau >= 6:
                        eleve.actif = False
                        eleve.date_sortie = date.today()
                        eleve.save(update_fields=["actif", "date_sortie"])
                        classe_destination = "Sorti(e) / Diplômé(e)"
                    elif admis_final:
                        classe_sup = _classe_superieure(classe)
                        eleve.classroom = classe_sup
                        eleve.save(update_fields=["classroom"])
                        classe_destination = classe_sup.nom
                    else:
                        classe_destination = classe.nom

                    resultats.append({
                        "eleve_id": eleve.pk,
                        "eleve": f"{eleve.first_name} {eleve.last_name}",
                        "classe_origine": classe.nom,
                        "moyenne": str(ligne["moyenne"]),
                        "decision": "admis" if admis_final else "redouble",
                        "classe_destination": classe_destination,
                    })

            PromotionCampagne.objects.create(
                annee_scolaire_cloturee=annee_scolaire,
                realisee_par=request.user,
                resultats=resultats,
            )

            ecole = EcoleConfig.get_solo()
            ecole.annee_scolaire_active = annee_suivante(annee_scolaire)
            ecole.save(update_fields=["annee_scolaire_active"])

        messages.success(
            request,
            f"Passage en classe supérieure confirmé pour {len(resultats)} élève(s) "
            f"({annee_scolaire}). Nouvelle année scolaire active : "
            f"{ecole.annee_scolaire_active}.",
        )

        return redirect("accounts:parametres")

    context = {
        "classes_info": classes_info,
        "annee_scolaire": annee_scolaire,
        "seuil_passage": SEUIL_PASSAGE,
    }

    return render(request, "bulletin/passage_annee.html", context)


@login_required
def passage_annee_export_csv(request):
    if not est_admin(request.user):
        messages.error(request, "Seul l'administrateur peut exporter cette liste.")
        return redirect("accounts:dashboard")

    annee_scolaire = request.GET.get("annee_scolaire") or annee_active()

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="passage_{annee_scolaire}.csv"'
    response.write("﻿")  # BOM pour un affichage correct des accents dans Excel

    writer = csv.writer(response)
    writer.writerow(["Classe", "Élève", "Moyenne annuelle /10", "Décision"])

    for info in _classes_avec_moyennes(annee_scolaire):
        for ligne in info["lignes"]:
            writer.writerow([
                info["classe"].nom,
                f"{ligne['eleve'].first_name} {ligne['eleve'].last_name}",
                str(ligne["moyenne"]),
                "Admis" if ligne["admis"] else "Redouble",
            ])

    return response
