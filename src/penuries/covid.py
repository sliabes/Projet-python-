"""Comparaison de la crise des carburants avec une vraie épidémie : le COVID-19 en 2020.

Source : Santé publique France, « Données hospitalières relatives à l'épidémie de COVID-19 »
(SI-VIC), fichier des nouvelles hospitalisations quotidiennes par département
(covid-hospit-incid), publié sur data.gouv.fr.

Méthode : on compare la FORME des courbes, pas leur niveau. Chaque série est lissée sur
7 jours, puis on mesure combien de temps elle met à monter de la moitié de son pic jusqu'au
pic, et à redescendre du pic jusqu'à la moitié de son pic.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests

# Lien stable data.gouv.fr vers covid-hospit-incid (nouvelles hospitalisations par département et par jour)
URL_HOSPITALISATIONS = "https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c"

VAGUES_COVID = {
    "COVID-19, 1re vague (printemps 2020)": ("2020-03-19", "2020-06-30"),
    "COVID-19, 2e vague (automne 2020)": ("2020-08-15", "2020-12-31"),
}

COULEURS = {
    "carburant": "#2a5db0",
    "COVID-19, 1re vague (printemps 2020)": "#d97706",
    "COVID-19, 2e vague (automne 2020)": "#6b7280",
}


# ---------------------------------------------------------------------------
# Collecte
# ---------------------------------------------------------------------------

def telecharger_hospitalisations(dossier: str = "data/brut") -> Path:
    """Télécharge le fichier des nouvelles hospitalisations COVID (une seule fois)."""
    chemin = Path(dossier) / "covid_hospit_incid.csv"
    if chemin.exists():
        return chemin
    chemin.parent.mkdir(parents=True, exist_ok=True)
    reponse = requests.get(URL_HOSPITALISATIONS, timeout=120)
    reponse.raise_for_status()
    chemin.write_bytes(reponse.content)
    return chemin


def lire_hospitalisations(chemin: Path) -> pd.DataFrame:
    """Lit le fichier (séparateur « ; »), garde la France métropolitaine et convertit les dates."""
    df = pd.read_csv(chemin, sep=";", dtype={"dep": str})
    if df.shape[1] == 1:  # au cas où le séparateur serait une virgule
        df = pd.read_csv(chemin, sep=",", dtype={"dep": str})
    colonnes_attendues = {"dep", "jour", "incid_hosp"}
    manquantes = colonnes_attendues - set(df.columns)
    if manquantes:
        raise ValueError(f"Colonnes absentes du fichier COVID : {manquantes}. Colonnes lues : {list(df.columns)}")

    df["jour"] = pd.to_datetime(df["jour"], errors="coerce")
    if df["jour"].isna().mean() > 0.5:  # dates au format jj/mm/aaaa
        df["jour"] = pd.to_datetime(df["jour"].astype(str), dayfirst=True, errors="coerce")
    df = df.dropna(subset=["jour"])
    return df[~df["dep"].str.startswith("97")]  # métropole uniquement, comme pour les carburants


def serie_nationale(df_hosp: pd.DataFrame) -> pd.Series:
    """Nombre de nouvelles hospitalisations par jour, en France métropolitaine."""
    return df_hosp.groupby("jour")["incid_hosp"].sum().sort_index().rename("nouvelles_hospitalisations")


# ---------------------------------------------------------------------------
# Indicateurs de forme
# ---------------------------------------------------------------------------

def lisser(serie: pd.Series, fenetre: int = 7) -> pd.Series:
    """Moyenne mobile centrée sur 7 jours, pour effacer les effets de jour de la semaine."""
    return serie.rolling(fenetre, center=True, min_periods=fenetre // 2 + 1).mean()


def caracteriser_vague(serie_lissee: pd.Series, debut: str, fin: str) -> dict:
    """Date et valeur du pic, temps de montée (mi-hauteur → pic), temps de descente
    (pic → mi-hauteur), asymétrie (descente / montée)."""
    s = serie_lissee.loc[debut:fin].dropna()
    date_pic = s.idxmax()
    mi_hauteur = s.max() / 2

    avant = s.loc[:date_pic]
    sous_moitie_avant = avant[avant < mi_hauteur]
    jours_montee = (date_pic - sous_moitie_avant.index[-1]).days if len(sous_moitie_avant) else None

    apres = s.loc[date_pic:]
    sous_moitie_apres = apres[apres < mi_hauteur]
    jours_descente = (sous_moitie_apres.index[0] - date_pic).days if len(sous_moitie_apres) else None

    asymetrie = jours_descente / jours_montee if jours_montee and jours_descente else None
    return {
        "date_du_pic": date_pic.date(),
        "valeur_au_pic": round(s.max()),
        "jours_de_montee": jours_montee,
        "jours_de_descente": jours_descente,
        "asymetrie_descente_sur_montee": round(asymetrie, 1) if asymetrie else None,
    }


def courbe_normalisee(serie_lissee: pd.Series, debut: str, fin: str) -> pd.DataFrame:
    """Recentre la courbe sur son pic (jour 0) et la divise par la valeur du pic (1 = pic)."""
    s = serie_lissee.loc[debut:fin].dropna()
    date_pic = s.idxmax()
    return pd.DataFrame({
        "jours_depuis_pic": (s.index - date_pic).days,
        "valeur_relative": (s / s.max()).to_numpy(),
    })


def comparer_formes(serie_carburant: pd.Series, serie_covid: pd.Series, periode_carburant: tuple) -> tuple:
    """Construit le tableau des indicateurs de forme et les courbes normalisées
    pour la crise des carburants et les deux vagues de COVID."""
    carburant = lisser(serie_carburant)
    covid = lisser(serie_covid)
    series = {"Carburants 2022 : nouvelles ruptures": (carburant, periode_carburant)}
    series.update({nom: (covid, periode) for nom, periode in VAGUES_COVID.items()})

    tableau = pd.DataFrame({nom: caracteriser_vague(s, *p) for nom, (s, p) in series.items()}).T
    courbes = {nom: courbe_normalisee(s, *p) for nom, (s, p) in series.items()}
    return tableau, courbes


# ---------------------------------------------------------------------------
# Graphique
# ---------------------------------------------------------------------------

def graphique_comparaison(courbes: dict, jours_avant: int = 45, jours_apres: int = 75):
    """G8 : les courbes normalisées superposées, alignées sur leur pic."""
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for nom, courbe in courbes.items():
        courbe = courbe[courbe["jours_depuis_pic"].between(-jours_avant, jours_apres)]
        couleur = COULEURS["carburant"] if "carburant" in nom else COULEURS.get(nom, "#111827")
        epaisseur = 2.6 if "carburant" in nom else 2
        ax.plot(courbe["jours_depuis_pic"], courbe["valeur_relative"], color=couleur,
                linewidth=epaisseur, label=nom)

    ax.axvline(0, color="#111827", linewidth=0.8)
    ax.axhline(0.5, color="#9ca3af", linewidth=1, linestyle="--")
    ax.text(-jours_avant + 1, 0.52, "mi-hauteur", color="#6b7280", fontsize=9)
    ax.text(1, 1.03, "pic", color="#111827", fontsize=9)

    ax.set_xlim(-jours_avant, jours_apres)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("Jours avant (–) et après (+) le pic")
    ax.set_ylabel("Nouveaux cas, en proportion du pic\n(moyenne mobile sur 7 jours)")
    ax.set_title("La crise des carburants a-t-elle la forme d'une épidémie ?", loc="left",
                 fontsize=13, fontweight="bold")
    ax.legend(frameon=False, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return fig