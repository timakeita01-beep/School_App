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

    path(
        "<int:pk>/pdf/",
        views.bulletin_pdf,
        name="pdf"
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

    path(
        "parent/<uuid:token>/bulletin/<int:pk>/pdf/",
        views.bulletin_pdf_public,
        name="bulletin_pdf_public"
    ),

    path(
        "parent/<uuid:token>/bulletin/<int:pk>/matiere/<int:matiere_id>/signaler/",
        views.reclamation_creer,
        name="reclamation_creer"
    ),

    # Réclamations sur les notes (admin / enseignant)
    path(
        "reclamations/",
        views.reclamations_liste,
        name="reclamations"
    ),

    path(
        "reclamations/<int:pk>/transmettre/",
        views.reclamation_transmettre,
        name="reclamation_transmettre"
    ),

    path(
        "reclamations/<int:pk>/appliquer/",
        views.reclamation_appliquer,
        name="reclamation_appliquer"
    ),

    path(
        "reclamations/enseignant/",
        views.reclamations_enseignant,
        name="reclamations_enseignant"
    ),

    path(
        "reclamations/<int:pk>/valider/",
        views.reclamation_valider,
        name="reclamation_valider"
    ),

    path(
        "reclamations/<int:pk>/rejeter/",
        views.reclamation_rejeter,
        name="reclamation_rejeter"
    ),

    # Fin d'année : passage en classe supérieure
    path(
        "passage-annee/",
        views.passage_annee,
        name="passage_annee"
    ),

    path(
        "passage-annee/export/",
        views.passage_annee_export_csv,
        name="passage_annee_export_csv"
    ),
]
