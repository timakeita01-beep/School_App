from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Eleve, Parent
from .forms import EleveForm, ParentForm


# ─────────────────────────────────────────────
#  LISTE DES ÉLÈVES
# ─────────────────────────────────────────────
def liste_eleves(request):
    eleves = Eleve.objects.select_related('classe', 'parent')

    total_eleves  = eleves.count()
    total_garcons = eleves.filter(sexe='M').count()
    total_filles  = eleves.filter(sexe='F').count()
    moyenne_generale = 14.5  # valeur fixe en attendant les notes

    return render(request, 'eleves/liste_eleves.html', {
        'eleves': eleves,
        'total_eleves': total_eleves,
        'total_garcons': total_garcons,
        'total_filles': total_filles,
        'moyenne_generale': moyenne_generale,
    })


# ─────────────────────────────────────────────
#  DÉTAIL D'UN ÉLÈVE
# ─────────────────────────────────────────────
def detail_eleve(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)

    # Calcul de l'âge
    today = timezone.now().date()
    age = today.year - eleve.date_naissance.year - (
        (today.month, today.day) < (eleve.date_naissance.month, eleve.date_naissance.day)
    )

    return render(request, 'eleves/detail_eleve.html', {
        'eleve': eleve,
        'age':   age,
        'onglet': 'apercu',  # onglet actif par défaut
    })


# ─────────────────────────────────────────────
#  AJOUTER UN ÉLÈVE
# ─────────────────────────────────────────────
def ajouter_eleve(request):
    form = EleveForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        form.save()
        messages.success(request, "L'élève a été ajouté avec succès.")
        return redirect('liste_eleves')

    return render(request, 'eleves/ajouter_eleve.html', {'form': form})


# ─────────────────────────────────────────────
#  MODIFIER UN ÉLÈVE
# ─────────────────────────────────────────────
def modifier_eleve(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    form  = EleveForm(request.POST or None, request.FILES or None, instance=eleve)

    if form.is_valid():
        form.save()
        messages.success(request, "Les informations ont été mises à jour.")
        return redirect('detail_eleve', pk=eleve.pk)

    return render(request, 'eleves/modifier_eleve.html', {
        'form':  form,
        'eleve': eleve,
    })


# ─────────────────────────────────────────────
#  SUPPRIMER UN ÉLÈVE
# ─────────────────────────────────────────────
def supprimer_eleve(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)

    if request.method == 'POST':
        nom_complet = f"{eleve.nom} {eleve.prenom}"
        eleve.delete()
        messages.success(request, f"L'élève {nom_complet} a été supprimé.")
        return redirect('liste_eleves')

    return redirect('detail_eleve', pk=pk)


# ─────────────────────────────────────────────
#  LISTE DES PARENTS
# ─────────────────────────────────────────────
def liste_parents(request):
    parents = Parent.objects.prefetch_related('enfants').order_by('nom')
    return render(request, 'eleves/liste_parents.html', {'parents': parents})


# ─────────────────────────────────────────────
#  AJOUTER UN PARENT
# ─────────────────────────────────────────────
def ajouter_parent(request):
    form = ParentForm(request.POST or None)

    if form.is_valid():
        form.save()
        messages.success(request, "Le parent a été enregistré avec succès.")
        return redirect('liste_parents')

    return render(request, 'eleves/ajouter_parent.html', {'form': form})


# ─────────────────────────────────────────────
#  MODIFIER UN PARENT
# ─────────────────────────────────────────────
def modifier_parent(request, pk):
    parent = get_object_or_404(Parent, pk=pk)
    form   = ParentForm(request.POST or None, instance=parent)

    if form.is_valid():
        form.save()
        messages.success(request, "Les informations du parent ont été mises à jour.")
        return redirect('liste_parents')

    return render(request, 'eleves/modifier_parent.html', {
        'form':   form,
        'parent': parent,
    })


# ─────────────────────────────────────────────
#  SUPPRIMER UN PARENT
# ─────────────────────────────────────────────
def supprimer_parent(request, pk):
    parent = get_object_or_404(Parent, pk=pk)

    if request.method == 'POST':
        nom = parent.nom
        parent.delete()
        messages.success(request, f"Le parent {nom} a été supprimé.")
        return redirect('liste_parents')

    return redirect('liste_parents')