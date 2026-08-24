from django.contrib import admin
from .models import Matiere
 
@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ("nom", "note_sur", "coefficient")
    filter_horizontal = ("classes",)
    search_fields = ("nom",)
 