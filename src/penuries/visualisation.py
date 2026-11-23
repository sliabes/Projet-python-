"""Fonctions de graphiques communes au projet."""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

COULEUR_PRINCIPALE = "#2a5db0"
COULEUR_REPERE = "#6b7280"


def _style_axe(ax):
    """Style sobre commun : grille légère, pas de cadre haut et droit."""
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)


def courbe_epidemique(
    df_prev: pd.DataFrame,
    niveau_normal: float | None = None,
    dates_cles: dict[str, str] | None = None,
    titre: str = "La crise des carburants d'octobre 2022 vue comme une épidémie",
):
    """G1 : prévalence (en haut) et nouvelles ruptures (en bas), sur le même axe des dates."""
    fig, (ax_prev, ax_inc) = plt.subplots(
        2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [3, 2]}
    )

    # Panneau du haut : part de stations en rupture
    ax_prev.plot(df_prev["jour"], df_prev["pct_en_rupture"], color=COULEUR_PRINCIPALE, linewidth=2)
    if niveau_normal is not None:
        ax_prev.axhline(niveau_normal, color=COULEUR_REPERE, linestyle="--", linewidth=1)
        ax_prev.text(df_prev["jour"].iloc[0], niveau_normal + 1,
                     f"niveau normal de septembre ({niveau_normal:.1f} %)", color=COULEUR_REPERE, fontsize=9)
    ax_prev.set_ylim(0, df_prev["pct_en_rupture"].max() * 1.15)
    ax_prev.set_ylabel("Stations en rupture\nd'au moins un carburant (%)")
    ax_prev.set_title(titre, loc="left", fontsize=13, fontweight="bold")

    # Panneau du bas : nouvelles ruptures par jour
    ax_inc.bar(df_prev["jour"], df_prev["nouvelles_ruptures"], color=COULEUR_PRINCIPALE, alpha=0.75, width=0.8)
    ax_inc.set_ylabel("Nouvelles stations\nen rupture (par jour)")
    ax_inc.set_xlabel("Date (relevé quotidien à 13 h)")

    # Annotation des deux pics
    pic_prev = df_prev.loc[df_prev["pct_en_rupture"].idxmax()]
    pic_inc = df_prev.loc[df_prev["nouvelles_ruptures"].idxmax()]
    ax_prev.annotate(f"pic : {pic_prev['pct_en_rupture']:.1f} % le {pic_prev['jour']:%d/%m}",
                     xy=(pic_prev["jour"], pic_prev["pct_en_rupture"]), xytext=(10, 5),
                     textcoords="offset points", fontsize=9)
    ax_inc.annotate(f"pic : {pic_inc['nouvelles_ruptures']} stations le {pic_inc['jour']:%d/%m}",
                    xy=(pic_inc["jour"], pic_inc["nouvelles_ruptures"]), xytext=(10, -5),
                    textcoords="offset points", fontsize=9)

    # Dates clés, sur les deux panneaux
    for date, libelle in (dates_cles or {}).items():
        for ax in (ax_prev, ax_inc):
            ax.axvline(pd.Timestamp(date), color=COULEUR_REPERE, linestyle=":", linewidth=1)
        ax_prev.text(pd.Timestamp(date), ax_prev.get_ylim()[1] * 0.98, f" {libelle}",
                     rotation=90, va="top", fontsize=8, color=COULEUR_REPERE)

    for ax in (ax_prev, ax_inc):
        _style_axe(ax)
    ax_inc.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax_inc.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    fig.tight_layout()
    return fig