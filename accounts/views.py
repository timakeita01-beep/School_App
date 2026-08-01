from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from eleves.models import Student
from classes.models import Classe
from matieres.models import Matiere

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
    repartition_classes = Classe.objects.annotate(total=models.Count('students'))
    max_eleves = repartition_classes.aggregate(models.Max('total'))['total__max'] or 1
    
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

    return render(request, "accounts/teacher_dashboard.html")


def teacher_list(request):
    # Logique pour récupérer la liste des enseignants
    teachers = User.objects.filter(groups__name='Teacher')
    return render(request, 'accounts/teacher_list.html', {'teachers': teachers})
