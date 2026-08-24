from django import forms
from .models import Matiere
 
 
class MatiereForm(forms.ModelForm):
    class Meta:
        model = Matiere
        fields = ["nom", "description", "note_sur", "coefficient", "classes"]
        widgets = {
            "nom": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ex: Calcul, Lecture, Écriture..."
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control", "rows": 3
            }),
            "note_sur": forms.NumberInput(attrs={
                "class": "form-control", "min": 5, "step": 5
            }),
            "coefficient": forms.NumberInput(attrs={
                "class": "form-control", "min": 1
            }),
            "classes": forms.CheckboxSelectMultiple(),
        }
        labels = {
            "note_sur": "Notée sur",
            "classes": "Classes concernées",
        }