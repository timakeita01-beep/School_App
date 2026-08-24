from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.db import models
from eleves.models import Student
from classes.models import Classe
from matieres.models import Matiere
from .models import EcoleConfig

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect("accounts:dashboard")
    
    # Statistiques
    total_eleves = Student.objects.count()
    total_enseignants = User.objects.filter(groups__name='Teacher').count()
    total_classes = Classe.objects.count()
    total_matieres = Matiere.objects.count()
    
    # Derniers élèves inscrits
    derniers_eleves = Student.objects.all().order_by('-inscription_date')[:5]
    
    # Répartition des classes
    repartition_classes = Classe.objects.annotate(
    total=models.Count('students'))
    max_eleves = repartition_classes.aggregate(
    models.Max('total')
    )['total__max'] or 1

    for classe in repartition_classes:
      classe.pourcentage = (classe.total / max_eleves) * 100
    
    context = {
        'total_eleves': total_eleves,
        'total_enseignants': total_enseignants,
        'total_classes': total_classes,
        'total_matieres': total_matieres,
        'derniers_eleves': derniers_eleves,
        'repartition_classes': repartition_classes,
        'max_eleves': max_eleves,
    }
    
    return render(request, "accounts/admin_dashboard.html", context)


def home(request):
    return render(request, "accounts/home.html")

def is_teacher(user):
    return user.groups.filter(name="Teacher").exists()

def is_admin(user):
    return user.is_staff

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("accounts:admin_dashboard")
        else:
            return render(request, "accounts/login.html", {
                "error": "Nom ou mot de passe incorrect"
            })

    return render(request, "accounts/login.html")

def logout_view(request):
    logout(request)
    return redirect("accounts:login")

@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect("accounts:admin_dashboard")
    else:
        return redirect("accounts:teacher_dashboard")


def teacher_dashboard(request):
    if request.user.is_staff:
        return redirect("accounts:admin_dashboard")

    from bulletins.models import Note
    from bulletins.utils import mois_courant, mois_label, ANNEE_SCOLAIRE_DEFAUT

    classes = Classe.objects.filter(enseignant=request.user).order_by("-niveau", "nom")

    mois = mois_courant()
    annee_scolaire = ANNEE_SCOLAIRE_DEFAUT

    classes_info = []

    for classe in classes:
        total_eleves = classe.students.count()
        matieres = classe.matieres.all()
        total_matieres = matieres.count()

        matieres_completes = 0
        for matiere in matieres:
            notes_count = Note.objects.filter(
                matiere=matiere,
                mois=mois,
                annee_scolaire=annee_scolaire,
                student__classroom=classe,
            ).count()
            if total_eleves and notes_count == total_eleves:
                matieres_completes += 1

        classes_info.append({
            "classe": classe,
            "total_eleves": total_eleves,
            "total_matieres": total_matieres,
            "matieres_completes": matieres_completes,
            "matieres_restantes": total_matieres - matieres_completes,
        })

    context = {
        "classes_info": classes_info,
        "mois": mois,
        "mois_label": mois_label(mois),
        "annee_scolaire": annee_scolaire,
    }

    return render(request, "accounts/teacher_dashboard.html", context)


def teacher_list(request):
    teachers = User.objects.filter(
        groups__name="Teacher"
    ).distinct()

    return render(request, "accounts/teacher_list.html", {
        "teachers": teachers
    })


# AJOUTER UN ENSEIGNANT
def teacher_create(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        # Vérification du nom d'utilisateur
        if not username:
            messages.error(
                request,
                "Le nom d'utilisateur est obligatoire."
            )
            return redirect("accounts:teacher_create")

        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "Ce nom d'utilisateur existe déjà."
            )
            return redirect("accounts:teacher_create")

        # Vérification du mot de passe
        if not password:
            messages.error(
                request,
                "Le mot de passe est obligatoire."
            )
            return redirect("accounts:teacher_create")

        if password != password_confirm:
            messages.error(
                request,
                "Les mots de passe ne correspondent pas."
            )
            return redirect("accounts:teacher_create")

        # Création de l'utilisateur
        teacher = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )

        # Récupération/création du groupe Teacher
        teacher_group, created = Group.objects.get_or_create(
            name="Teacher"
        )

        # Ajout automatique au groupe Teacher
        teacher.groups.add(teacher_group)

        messages.success(
            request,
            f"L'enseignant « {teacher.get_full_name() or teacher.username} » "
            "a été ajouté avec succès."
        )

        return redirect("accounts:teacher_list")

    return render(
        request,
        "accounts/teacher_create.html"
    )

# MODIFIER UN ENSEIGNANT
def teacher_update(request, pk):

    teacher = get_object_or_404(
        User.objects.filter(groups__name="Teacher").distinct(),
        pk=pk
    )

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        # Vérification du nom d'utilisateur
        if not username:
            messages.error(
                request,
                "Le nom d'utilisateur est obligatoire."
            )
            return redirect(
                "accounts:teacher_update",
                pk=teacher.pk
            )

        # Vérifier que le username n'est pas déjà utilisé
        if User.objects.filter(
            username=username
        ).exclude(pk=teacher.pk).exists():

            messages.error(
                request,
                "Ce nom d'utilisateur est déjà utilisé."
            )

            return redirect(
                "accounts:teacher_update",
                pk=teacher.pk
            )

        # Vérifier les mots de passe seulement si l'utilisateur
        # souhaite modifier le mot de passe
        if password:

            if password != password_confirm:
                messages.error(
                    request,
                    "Les mots de passe ne correspondent pas."
                )

                return redirect(
                    "accounts:teacher_update",
                    pk=teacher.pk
                )

            teacher.set_password(password)

        # Modification des informations
        teacher.username = username
        teacher.first_name = first_name
        teacher.last_name = last_name
        teacher.email = email

        teacher.save()

        # S'assurer qu'il appartient toujours au groupe Teacher
        teacher_group, created = Group.objects.get_or_create(
            name="Teacher"
        )

        teacher.groups.add(teacher_group)

        messages.success(
            request,
            f"L'enseignant « {teacher.get_full_name() or teacher.username} » "
            "a été modifié avec succès."
        )

        return redirect("accounts:teacher_list")

    return render(
        request,
        "accounts/teacher_update.html",
        {
            "teacher": teacher
        }
    )
# SUPPRIMER UN ENSEIGNANT
def teacher_delete(request, pk):

    teacher = get_object_or_404(
        User.objects.filter(groups__name="Teacher").distinct(),
        pk=pk
    )

    nom = teacher.get_full_name() or teacher.username

    teacher.delete()

    messages.success(
        request,
        f"L'enseignant « {nom} » a été supprimé avec succès."
    )

    return redirect("accounts:teacher_list")


@login_required
def parametres(request):
    if not request.user.is_staff:
        messages.error(request, "Seul l'administrateur peut modifier ces paramètres.")
        return redirect("accounts:dashboard")

    ecole = EcoleConfig.get_solo()

    if request.method == "POST":
        ecole.nom = request.POST.get("nom", "").strip()
        ecole.adresse = request.POST.get("adresse", "").strip()
        ecole.contact = request.POST.get("contact", "").strip()
        ecole.nom_directeur = request.POST.get("nom_directeur", "").strip()
        ecole.save()

        messages.success(request, "Les paramètres de l'établissement ont été enregistrés.")
        return redirect("accounts:parametres")

    return render(request, "accounts/parametres.html", {"ecole": ecole})


def teacher_profile(request, pk):
    teacher = get_object_or_404(
        User.objects.filter(groups__name="Teacher").distinct(),
        pk=pk
    )

    # Classes affectées à cet enseignant
    classes = Classe.objects.filter(
        enseignant=teacher
    ).order_by("-niveau")

    context = {
        "teacher": teacher,
        "classes": classes,
    }

    return render(
        request,
        "accounts/teacher_profile.html",
        context
    )