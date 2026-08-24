from datetime import date
from urllib.parse import quote

# Indicatif pays utilisé par défaut si le numéro du parent n'en contient pas
# déjà un (Mali).
INDICATIF_PAYS_DEFAUT = "223"

# Mois de l'année scolaire, dans l'ordre (Septembre -> Juin)
MOIS_SCOLAIRE = [
    (9, "Septembre"),
    (10, "Octobre"),
    (11, "Novembre"),
    (12, "Décembre"),
    (1, "Janvier"),
    (2, "Février"),
    (3, "Mars"),
    (4, "Avril"),
    (5, "Mai"),
    (6, "Juin"),
]

MOIS_LABELS = dict(MOIS_SCOLAIRE)

ANNEE_SCOLAIRE_DEFAUT = "2026-2027"


def mois_courant():
    """Mois scolaire courant, ou Septembre si on est hors année scolaire (juillet/août)."""
    m = date.today().month
    return m if m in MOIS_LABELS else 9


def mois_label(mois):
    return MOIS_LABELS.get(int(mois), str(mois))


def lien_whatsapp(numero, message):
    """Construit un lien wa.me (« click to chat ») ouvrant une conversation
    WhatsApp avec ce numéro et ce message pré-rempli. Ne joint aucun fichier :
    WhatsApp ne le permet pas via un simple lien, seule son API Business
    payante le pourrait."""

    if not numero:
        return None

    chiffres = "".join(c for c in numero if c.isdigit())

    if not chiffres:
        return None

    # Si le numéro ne semble pas déjà contenir un indicatif pays (numéro
    # local à 8 chiffres, format malien courant), on l'ajoute.
    if len(chiffres) <= 8:
        chiffres = INDICATIF_PAYS_DEFAUT + chiffres

    return f"https://wa.me/{chiffres}?text={quote(message)}"
