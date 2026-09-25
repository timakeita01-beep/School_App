from io import BytesIO

from django.template.loader import render_to_string
from xhtml2pdf import pisa


def generer_bulletin_pdf(contexte):
    """Génère le PDF d'un bulletin à partir du contexte déjà construit par
    _contexte_bulletin() (mêmes clés que pour l'affichage HTML). Retourne
    les octets du PDF, ou None en cas d'échec de rendu."""

    html = render_to_string("bulletin/bulletin_pdf.html", contexte)
    buffer = BytesIO()

    resultat = pisa.CreatePDF(src=html, dest=buffer)

    if resultat.err:
        return None

    return buffer.getvalue()


def nom_fichier_pdf(bulletin):
    from .utils import mois_label

    eleve = bulletin.student
    return (
        f"Bulletin_{eleve.last_name}_{eleve.first_name}_"
        f"{mois_label(bulletin.mois)}_{bulletin.annee_scolaire}.pdf"
    ).replace(" ", "_")
