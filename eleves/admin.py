from django.contrib import admin
from .models import Eleve, Parent


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'telephone', 'email')
    search_fields = ('nom', 'telephone', 'email')
    ordering      = ('nom',)


@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display  = ('nom', 'prenom', 'classe', 'sexe', 'statut', 'parent')
    list_filter   = ('classe', 'sexe', 'statut')
    search_fields = ('nom', 'prenom')
    ordering      = ('nom',)
