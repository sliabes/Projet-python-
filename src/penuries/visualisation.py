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
    titre: str = "G1 - La crise des carburants d'octobre 2022 vue comme une épidémie",
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
    ax_prev.set_title(titre, loc="center", fontsize=15, fontweight="bold")

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


def carte_chaleur_departements(df_prev_dep: pd.DataFrame, dates_decollage: pd.Series):
    """G2 : part de stations en rupture, une ligne par département, triées par date de décollage."""
    tableau = df_prev_dep.pivot(index="departement", columns="jour", values="pct_en_rupture")
    ordre = dates_decollage.sort_values(na_position="last").index
    tableau = tableau.loc[ordre]

    fig, ax = plt.subplots(figsize=(12, 13))
    image = ax.imshow(tableau.to_numpy(), aspect="auto", cmap="Blues", vmin=0, vmax=80,
                      interpolation="nearest")
    barre = fig.colorbar(image, ax=ax, shrink=0.5, pad=0.01)
    barre.set_label("Stations en rupture d'au moins un carburant (%)")

    ax.set_yticks(range(len(tableau)))
    ax.set_yticklabels(tableau.index, fontsize=6)
    ax.set_ylabel("Département (trié par date de décollage, du plus précoce au plus tardif)")

    jours = tableau.columns
    lundis = [i for i, jour in enumerate(jours) if jour.dayofweek == 0]
    ax.set_xticks(lundis)
    ax.set_xticklabels([jours[i].strftime("%d/%m") for i in lundis])
    ax.set_xlabel("Date (relevé quotidien à 13 h)")
    ax.set_title(" G2 - Quand chaque département bascule-t-il dans la pénurie ?", loc="center",
                 fontsize=15, fontweight="bold")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    
    return fig