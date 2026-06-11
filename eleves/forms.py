from django import forms
from .models import Eleve, Parent


# ─── Formulaire Élève ───────────────────────────────────────────────────
class EleveForm(forms.ModelForm):
    class Meta:
        model  = Eleve
        fields = ['nom', 'prenom', 'sexe', 'date_naissance', 'statut', 'classe', 'parent', 'image']

        widgets = {
            'nom':            forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex : SAIDU'}),
            'prenom':         forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex : Ezekiel'}),
            'sexe':           forms.Select(attrs={'class': 'form-input'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'statut':         forms.Select(attrs={'class': 'form-input'}),
            'classe':         forms.Select(attrs={'class': 'form-input'}),
            'parent':         forms.Select(attrs={'class': 'form-input'}),
            'image':          forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }

        labels = {
            'nom':            'Nom',
            'prenom':         'Prénom',
            'sexe':           'Sexe',
            'date_naissance': 'Date de naissance',
            'statut':         'Statut',
            'classe':         'Classe',
            'parent':         'Tuteur / Parent',
            'image':          'Photo de profil',
        }


# ─── Formulaire Parent ──────────────────────────────────────────────────
class ParentForm(forms.ModelForm):
    class Meta:
        model  = Parent
        fields = ['nom', 'telephone', 'email']

        widgets = {
            'nom':       forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex : SAIDU Mohamed',
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex : +224 621 00 00 00',
                'type': 'tel',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex : parent@email.com',
            }),
        }

        labels = {
            'nom':       'Nom complet',
            'telephone': 'Numéro de téléphone',
            'email':     'Adresse e-mail (optionnel)',
        }

    def clean_telephone(self):
        """Valide que le numéro n'est pas vide."""
        tel = self.cleaned_data.get('telephone', '').strip()
        if not tel:
            raise forms.ValidationError("Le numéro de téléphone est obligatoire.")
        return tel