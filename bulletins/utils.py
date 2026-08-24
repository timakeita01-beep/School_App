from datetime import date

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
