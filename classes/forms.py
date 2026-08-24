from django import forms
from .models import Classe
from django.contrib.auth.models import User

class ClasseForm(forms.ModelForm):

    enseignant = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True),
        empty_label="Choisir un enseignant"
    )

    class Meta:
        model = Classe
        fields = ['nom', 'enseignant']