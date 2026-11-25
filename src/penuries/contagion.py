"""Test de l'hypothèse H2 : les ruptures se transmettent-elles de station en station ?

Méthode : chaque jour, on regarde les stations « à risque » (pas en rupture la veille,
au moins une voisine à moins de 5 km). Une station est « exposée » si au moins une de
ses voisines était en rupture la veille. On compare la probabilité de tomber en rupture
des stations exposées et non exposées, en brut puis à département et jour fixés.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PERIODE_CRISE = ("2022-09-28", "2022-10-31")
PERIODE_NORMALE = ("2022-09-05", "2022-09-25")
OBSERVATIONS_MIN = 100  # en dessous, une classe d'exposition n'est pas tracée (estimation trop instable)

COULEUR_EXPOSEE = "#2a5db0"
COULEUR_NON_EXPOSEE = "#9ca3af"
COULEUR_TEXTE = "#111827"


# ---------------------------------------------------------------------------
# Calculs
# ---------------------------------------------------------------------------

def stations_a_risque(panel: pd.DataFrame, debut: str, fin: str) -> pd.DataFrame:
    """Garde, pour chaque jour de la période, les stations qui n'étaient pas en rupture
    la veille et qui ont au moins une voisine. Ajoute :
    - tombe_en_rupture : 1 si la station est en rupture le jour même ;
    - exposee : au moins une voisine en rupture la veille ;
    - part_voisines_en_rupture_veille : part des voisines en rupture la veille ;
    - ecart_dep_jour : écart (en points de %) au taux de rupture moyen des stations
      à risque du même département le même jour.

    Le panel doit contenir en_rupture, nb_voisines et nb_voisines_en_rupture
    (voir indicateurs.ajouter_voisines_en_rupture).
    """
    panel = panel.sort_values(["id_station", "jour"]).copy()
    par_station = panel.groupby("id_station")
    panel["en_rupture_veille"] = par_station["en_rupture"].shift(1, fill_value=True).astype(bool)
    panel["nb_voisines_en_rupture_veille"] = par_station["nb_voisines_en_rupture"].shift(1, fill_value=0)

    a_risque = (
        ~panel["en_rupture_veille"]
        & (panel["nb_voisines"] > 0)
        & panel["jour"].between(debut, fin)
    )
    df = panel[a_risque].copy()

    df["tombe_en_rupture"] = df["en_rupture"].astype(int)
    df["exposee"] = df["nb_voisines_en_rupture_veille"] >= 1
    df["part_voisines_en_rupture_veille"] = df["nb_voisines_en_rupture_veille"] / df["nb_voisines"]

    taux_dep_jour = df.groupby(["departement", "jour"])["tombe_en_rupture"].transform("mean")
    df["ecart_dep_jour"] = 100 * (df["tombe_en_rupture"] - taux_dep_jour)
    return df


def taux_attaque(df_risque: pd.DataFrame, par: str = "exposee") -> pd.DataFrame:
    """Taux d'attaque brut (%) et écart moyen au département (points) par groupe."""
    return (
        df_risque.groupby(par, observed=True)
        .agg(
            taux_attaque_pct=("tombe_en_rupture", "mean"),
            ecart_dep_jour_pts=("ecart_dep_jour", "mean"),
            nb_observations=("tombe_en_rupture", "size"),
        )
        .assign(taux_attaque_pct=lambda d: 100 * d["taux_attaque_pct"])
    )


def ajouter_classe_exposition(df_risque: pd.DataFrame) -> pd.DataFrame:
    """Classe la part de voisines en rupture la veille, pour l'effet dose-réponse."""
    df = df_risque.copy()
    df["classe_exposition"] = pd.cut(
        df["part_voisines_en_rupture_veille"],
        bins=[-0.001, 0, 0.25, 0.5, 0.75, 1],
        labels=["aucune", "jusqu'à 25 %", "25 à 50 %", "50 à 75 %", "plus de 75 %"],
    )
    return df


def analyser_h2(panel: pd.DataFrame) -> dict:
    """Enchaîne tout le test H2 et renvoie les quatre tableaux de résultats."""
    risque_crise = ajouter_classe_exposition(stations_a_risque(panel, *PERIODE_CRISE))
    risque_normal = ajouter_classe_exposition(stations_a_risque(panel, *PERIODE_NORMALE))
    return {
        "taux_crise": taux_attaque(risque_crise),
        "taux_normal": taux_attaque(risque_normal),
        "dose_crise": taux_attaque(risque_crise, par="classe_exposition"),
        "dose_normal": taux_attaque(risque_normal, par="classe_exposition"),
    }


# ---------------------------------------------------------------------------
# Graphiques
# ---------------------------------------------------------------------------

def _style_axe(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)


def graphique_taux_attaque(taux_crise: pd.DataFrame, taux_normal: pd.DataFrame):
    """G5 : taux d'attaque selon qu'une voisine était en rupture la veille,
    en brut (à gauche) et à département et jour fixés (à droite)."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    periodes = ["Septembre (normal)", "Crise (28/09 – 31/10)"]
    x = np.arange(len(periodes))
    largeur = 0.38
    groupes = [
        (False, COULEUR_NON_EXPOSEE, "Aucune voisine en rupture la veille"),
        (True, COULEUR_EXPOSEE, "Au moins une voisine en rupture la veille"),
    ]
    panneaux = [
        (axes[0], "taux_attaque_pct", "Stations tombant en rupture\nle lendemain (%)", "Taux d'attaque brut"),
        (axes[1], "ecart_dep_jour_pts", "Écart au taux du département\nle même jour (points de %)",
         "À département et jour fixés"),
    ]
    for ax, colonne, ylabel, titre in panneaux:
        for k, (exposee, couleur, libelle) in enumerate(groupes):
            valeurs = [taux_normal.loc[exposee, colonne], taux_crise.loc[exposee, colonne]]
            barres = ax.bar(x + (k - 0.5) * largeur, valeurs, largeur, color=couleur, label=libelle)
            ax.bar_label(barres, fmt="%.1f", fontsize=9, padding=2)
        ax.axhline(0, color=COULEUR_TEXTE, linewidth=0.8)
        ax.set_xticks(x, periodes)
        ax.set_ylabel(ylabel)
        ax.set_title(titre, loc="left", fontsize=11, fontweight="bold")
        _style_axe(ax)
    axes[0].legend(frameon=False, loc="upper left", fontsize=9)
    fig.suptitle("Avoir une voisine en rupture augmente-t-il le risque de tomber en rupture ?",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig


def graphique_dose_reponse(dose_crise: pd.DataFrame, dose_normal: pd.DataFrame):
    """G6 : écart au taux du département selon la part de voisines en rupture la veille."""
    fig, ax = plt.subplots(figsize=(10, 5))
    series = [
        (dose_crise, COULEUR_EXPOSEE, "Crise (28/09 – 31/10)"),
        (dose_normal, COULEUR_NON_EXPOSEE, "Septembre (normal)"),
    ]
    for tab, couleur, libelle in series:
        tab = tab[tab["nb_observations"] >= OBSERVATIONS_MIN]  # classes trop petites : non tracées
        ax.plot([str(c) for c in tab.index], tab["ecart_dep_jour_pts"], marker="o", markersize=8,
                linewidth=2, color=couleur, label=libelle)
    ax.axhline(0, color=COULEUR_TEXTE, linewidth=0.8)
    ax.set_xlabel("Part des voisines (à moins de 5 km) en rupture la veille")
    ax.set_ylabel("Écart au taux de rupture du département\nle même jour (points de %)")
    ax.set_title("Plus les voisines sont en rupture, plus le risque augmente-t-il ?",
                 loc="left", fontsize=13, fontweight="bold")
    ax.legend(frameon=False)
    _style_axe(ax)
    fig.tight_layout()
    return fig