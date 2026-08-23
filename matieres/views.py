
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Matiere
from .forms import MatiereForm
 

 
def matiere_list(request):
    matieres = Matiere.objects.all().prefetch_related("classes")
    return render(request, "matieres.html", {"matieres": matieres})
 
 

def matiere_create(request):
    if request.method == "POST":
        form = MatiereForm(request.POST)
        if form.is_valid():
            matiere = form.save()
            messages.success(request, f"La matière « {matiere.nom} » a été créée avec succès.")
            return redirect("matieres:list")
    else:
        form = MatiereForm()
    return render(request, "ajouter_matiere.html", {
        "form": form,
        "titre": "Ajouter une matière",
    })
 

def matiere_update(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    if request.method == "POST":
        form = MatiereForm(request.POST, instance=matiere)
        if form.is_valid():
            form.save()
            messages.success(request, "Matière mise à jour avec succès.")
            return redirect("matieres:list")
    else:
        form = MatiereForm(instance=matiere)
    return render(request, "modifier_matiere.html", {
        "form": form,
        "matiere": matiere,
        "titre": f"Modifier {matiere.nom}",
    })
 

def matiere_delete(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    nom = matiere.nom
    matiere.delete()
    messages.success(request, f"La matière « {nom} » a été supprimée avec succès.")
    return redirect("matieres:list")
