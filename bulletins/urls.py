from django.urls import path

from . import views


app_name = "bulletin"


urlpatterns = [

    # Saisie des notes (enseignant)
    path(
        "classe/<int:classe_id>/mois/<int:mois>/",
        views.notes_classe,
        name="notes_classe"
    ),

    path(
        "classe/<int:classe_id>/mois/<int:mois>/matiere/<int:matiere_id>/enregistrer/",
        views.notes_bulk_save,
        name="notes_bulk_save"
    ),

    path(
        "note/<int:pk>/supprimer/",
        views.note_delete,
        name="note_delete"
    ),

    # Espace admin : classes, validation, notification
    path(
        "",
        views.bulletin_list,
        name="liste"
    ),

    path(
        "classe/<int:classe_id>/valider/",
        views.valider_classe,
        name="valider_classe"
    ),

    path(
        "classe/<int:classe_id>/notifier/",
        views.notifier_parents,
        name="notifier_parents"
    ),

    path(
        "<int:pk>/",
        views.bulletin_detail,
        name="detail"
    ),

    # Portail parent (public, sans connexion, via jeton personnel)
    path(
        "parent/<uuid:token>/",
        views.portail_parent,
        name="portail_parent"
    ),

    path(
        "parent/<uuid:token>/bulletin/<int:pk>/",
        views.bulletin_public,
        name="bulletin_public"
    ),
]
