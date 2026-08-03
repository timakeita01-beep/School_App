from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from .models import Matiere
from classes.models import Classe


def index(request):
    return redirect('classes_list')


def ajouter_matiere(request):
    if request.method != 'POST':
        return redirect('classes_list')

    nom = request.POST.get('nom', '').strip()
    coef = request.POST.get('coef', '').strip()
    classe_id = request.POST.get('classe_id')
    errors = {}

    if not nom:
        errors['nom'] = 'Le nom de la matière est requis.'
    if not coef:
        errors['coef'] = 'Le coefficient est requis.'
    elif not coef.isdigit() or int(coef) < 1:
        errors['coef'] = 'Le coefficient doit être un entier positif.'

    classe = None
    if not classe_id:
        errors['classe'] = 'La classe est requise.'
    else:
        try:
            classe = Classe.objects.get(pk=int(classe_id))
        except (ValueError, Classe.DoesNotExist):
            errors['classe'] = 'Classe invalide.'

    if errors:
        for error in errors.values():
            messages.error(request, error)
        return redirect(reverse('classes_list') + f'?selected={classe_id or ""}')

    Matiere.objects.create(nom=nom, coef=int(coef), classe=classe)
    messages.success(request, f'La matière « {nom} » a été ajoutée.')
    return redirect(reverse('classes_list') + f'?selected={classe.pk}')


def modifier_matiere(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    if request.method != 'POST':
        return redirect(reverse('classes_list') + f'?selected={matiere.classe.pk}')

    nom = request.POST.get('nom', '').strip()
    coef = request.POST.get('coef', '').strip()
    errors = {}

    if not nom:
        errors['nom'] = 'Le nom de la matière est requis.'
    if not coef:
        errors['coef'] = 'Le coefficient est requis.'
    elif not coef.isdigit() or int(coef) < 1:
        errors['coef'] = 'Le coefficient doit être un entier positif.'

    if errors:
        for error in errors.values():
            messages.error(request, error)
        return redirect(reverse('classes_list') + f'?selected={matiere.classe.pk}')

    matiere.nom = nom
    matiere.coef = int(coef)
    matiere.save()
    messages.success(request, f'La matière « {nom} » a été modifiée.')
    return redirect(reverse('classes_list') + f'?selected={matiere.classe.pk}')


def supprimer_matiere(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    classe_pk = matiere.classe.pk
    nom = matiere.nom
    matiere.delete()
    messages.success(request, f'La matière « {nom} » a été supprimée.')
    return redirect(reverse('classes_list') + f'?selected={classe_pk}')