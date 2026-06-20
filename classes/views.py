from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Classe

# Affichage de la liste des classes

def voir(request):
    classes = Classe.objects.all().order_by('-niveau')
    return render(request, 'classes.html', {'classes': classes})

# Ajouter une nouvelle classe

def ajouter_classe(request):
    context = {'errors': {}, 'nom': '', 'niveau': ''}

    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        niveau_str = request.POST.get('niveau', '').strip()

        context['nom'] = nom
        context['niveau'] = niveau_str

        # Validation
        if not nom:
            context['errors']['nom'] = "Le nom de la classe est requis."
        if not niveau_str:
            context['errors']['niveau'] = "Le niveau est requis."
        elif not niveau_str.isdigit() or int(niveau_str) < 1:
            context['errors']['niveau'] = "Le niveau doit être un nombre entier positif."

        if not context['errors']:
            Classe.objects.create(nom=nom, niveau=int(niveau_str))
            messages.success(request, f'La classe « {nom} » a été créée avec succès.')
            return redirect('classes_list')

    return render(request, 'ajouter_classe.html', context)


# Modifier une classe existante

def modifier_classe(request, pk):
    data = get_object_or_404(Classe, pk=pk)
    errors    = {}
    form_data = {'nom': data.nom, 'niveau': data.niveau}

    if request.method == 'POST':
        nom        = request.POST.get('nom', '').strip()
        niveau_str = request.POST.get('niveau', '').strip()
        form_data  = {'nom': nom, 'niveau': niveau_str}

        # Validation
        if not nom:
            errors['nom'] = "Le nom de la classe est requis."
        if not niveau_str:
            errors['niveau'] = "Le niveau est requis."
        elif not niveau_str.isdigit() or int(niveau_str) < 1:
            errors['niveau'] = "Le niveau doit être un nombre entier positif."

        if not errors:
            data.nom    = nom
            data.niveau = int(niveau_str)
            data.save()
            messages.success(request, f'La classe « {nom} » a été modifiée avec succès.')
            return redirect('classes_list')

    context = {'data': data, 'errors': errors, 'form_data': form_data}
    return render(request, 'modifier_classe.html', context)

# Supprimer une classe

def supprimer_classe(request, pk):
    data = get_object_or_404(Classe, pk=pk)
    nom  = data.nom
    data.delete()
    messages.success(request, f'La classe « {nom} » a été supprimée.')
    return redirect('classes_list')