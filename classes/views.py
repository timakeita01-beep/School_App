from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Classe
from django.contrib.auth.models import User


# Affichage de la liste des classes

def voir(request):
    classes = Classe.objects.all().order_by('-niveau')
    
    return render(request, 'classes.html', {'classes': classes})

def classe_detail(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    # Tous les élèves de cette classe
    eleves = classe.students.all()
    matieres = classe.matieres.all()

    enseignant = None
    if classe.enseignant:
        enseignant = classe.enseignant.get_full_name() or classe.enseignant.username

    context = {
        "classe": classe,
        "eleves": eleves,
        "matieres": matieres,
        "enseignant": enseignant,
        "eleves_filles": eleves.filter(sexe="F").count(),
        "eleves_garcons": eleves.filter(sexe="M").count(),
    }
    return render(request, "classe_detail.html", context)

# Ajouter une nouvelle classe

def ajouter_classe(request):
    context = {
        'errors': {},
        'nom': '',
        'niveau': '',
        'enseignants': User.objects.filter(groups__name="Teacher"),
    }

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        niveau_str = request.POST.get('niveau', '').strip()
        enseignant_id = request.POST.get('enseignant')

        context['nom'] = nom
        context['niveau'] = niveau_str

        if not nom:
            context['errors']['nom'] = "Le nom de la classe est requis."

        if not niveau_str:
            context['errors']['niveau'] = "Le niveau est requis."
        elif not niveau_str.isdigit() or int(niveau_str) < 1:
            context['errors']['niveau'] = "Le niveau doit être un nombre entier positif."

        enseignant = None
        if enseignant_id:
            try:
                enseignant = User.objects.get(id=enseignant_id)
            except User.DoesNotExist:
                context['errors']['enseignant'] = "Enseignant invalide."

        if not context['errors']:
            Classe.objects.create(
                nom=nom,
                niveau=int(niveau_str),
                enseignant=enseignant
            )

            messages.success(request, f'La classe « {nom} » a été créée avec succès.')
            return redirect('classes:list')

    return render(request, 'ajouter_classe.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Classe


def modifier_classe(request, pk):
    classe = get_object_or_404(Classe, pk=pk)

    errors = {}

    # Liste des enseignants
    enseignants = User.objects.filter(groups__name="Teacher")

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        niveau_str = request.POST.get("niveau", "").strip()
        enseignant_id = request.POST.get("enseignant")

        # Validation
        if not nom:
            errors["nom"] = "Le nom de la classe est requis."

        if not niveau_str:
            errors["niveau"] = "Le niveau est requis."
        elif not niveau_str.isdigit() or int(niveau_str) < 1:
            errors["niveau"] = "Le niveau doit être un nombre entier positif."

        enseignant = None

        if enseignant_id:
            try:
                enseignant = User.objects.get(
                    id=enseignant_id,
                    groups__name="Teacher"
                )
            except User.DoesNotExist:
                errors["enseignant"] = "Enseignant invalide."

        if not errors:
            classe.nom = nom
            classe.niveau = int(niveau_str)
            classe.enseignant = enseignant
            classe.save()

            messages.success(
                request,
                f"La classe « {classe.nom} » a été modifiée avec succès."
            )
            return redirect("classes:list")

        context = {
            "data": classe,
            "enseignants": enseignants,
            "errors": errors,
            "form_data": {
                "nom": nom,
                "niveau": niveau_str,
                "enseignant": enseignant_id,
            },
        }

        return render(request, "modifier_classe.html", context)

    # Affichage initial du formulaire
    context = {
        "data": classe,
        "enseignants": enseignants,
        "errors": {},
        "form_data": {
            "nom": classe.nom,
            "niveau": classe.niveau,
            "enseignant": classe.enseignant.id if classe.enseignant else "",
        },
    }

    return render(request, "modifier_classe.html", context)

# Supprimer une classe

def supprimer_classe(request, pk):
    data = get_object_or_404(Classe, pk=pk)
    nom  = data.nom
    data.delete()
    messages.success(request, f'La classe « {nom} » a été supprimée.')
    return redirect('classes:list')