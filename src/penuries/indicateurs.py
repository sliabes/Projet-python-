"""Indicateurs épidémiologiques appliqués aux ruptures de carburant."""

import pandas as pd

HEURE_RELEVE = pd.Timedelta(hours=13)  # heure des relevés du ministère


def panel_station_jour(
    df_ruptures: pd.DataFrame,
    df_stations: pd.DataFrame,
    date_debut: str = "2022-09-01",
    date_fin: str = "2022-11-30",
) -> pd.DataFrame:
    """Une ligne par station et par jour : la station a-t-elle une rupture en cours à 13 h ?"""
    jours = pd.date_range(date_debut, date_fin, freq="D")

    ruptures_par_jour = []
    for jour in jours:
        instant = jour + HEURE_RELEVE
        en_cours = (df_ruptures["debut"] <= instant) & (df_ruptures["fin"] > instant)
        ids = df_ruptures.loc[en_cours, "id_station"].unique()
        ruptures_par_jour.append(pd.DataFrame({"id_station": ids, "jour": jour}))
    df_en_rupture = pd.concat(ruptures_par_jour, ignore_index=True)
    df_en_rupture["en_rupture"] = True

    panel = pd.MultiIndex.from_product(
        [df_stations["id_station"], jours], names=["id_station", "jour"]
    ).to_frame(index=False)
    panel = panel.merge(df_en_rupture, on=["id_station", "jour"], how="left")
    panel["en_rupture"] = panel["en_rupture"].fillna(False).astype(bool)
    return panel.merge(df_stations[["id_station", "departement"]], on="id_station", how="left")


def ajouter_nouvelles_ruptures(panel: pd.DataFrame) -> pd.DataFrame:
    """Marque les stations qui passent en rupture ce jour-là (pas en rupture la veille)."""
    panel = panel.sort_values(["id_station", "jour"]).copy()
    veille = panel.groupby("id_station")["en_rupture"].shift(1, fill_value=False)
    panel["nouvelle_rupture"] = panel["en_rupture"] & ~veille
    return panel


def prevalence(panel: pd.DataFrame, par: str | None = None) -> pd.DataFrame:
    """% de stations en rupture chaque jour (nationale, ou par département si par='departement')."""
    cles = ["jour"] if par is None else ["jour", par]
    return (
        panel.groupby(cles)
        .agg(pct_en_rupture=("en_rupture", "mean"), nouvelles_ruptures=("nouvelle_rupture", "sum"))
        .assign(pct_en_rupture=lambda d: 100 * d["pct_en_rupture"])
        .reset_index()
    )
    

import numpy as np
from sklearn.neighbors import BallTree

RAYON_TERRE_KM = 6371.0


def paires_voisines(df_stations: pd.DataFrame, rayon_km: float = 5) -> pd.DataFrame:
    """Une ligne par couple (station, voisine) situées à moins de rayon_km l'une de l'autre.

    Les distances sont calculées « à vol d'oiseau » sur la sphère terrestre (formule de haversine),
    à l'aide d'un BallTree qui évite de comparer les 9 500 stations deux à deux.
    """
    coords = np.radians(df_stations[["latitude", "longitude"]].to_numpy())
    arbre = BallTree(coords, metric="haversine")
    indices, distances = arbre.query_radius(coords, r=rayon_km / RAYON_TERRE_KM, return_distance=True)

    ids = df_stations["id_station"].to_numpy()
    nb_par_station = [len(v) for v in indices]
    paires = pd.DataFrame({
        "id_station": np.repeat(ids, nb_par_station),
        "id_voisine": ids[np.concatenate(indices)],
        "distance_km": np.concatenate(distances) * RAYON_TERRE_KM,
    })
    return paires[paires["id_station"] != paires["id_voisine"]].reset_index(drop=True)


def ajouter_voisines_en_rupture(panel: pd.DataFrame, paires: pd.DataFrame) -> pd.DataFrame:
    """Ajoute au panel, pour chaque station et chaque jour :
    - nb_voisines : nombre de stations à moins de 5 km ;
    - nb_voisines_en_rupture : nombre de ces voisines en rupture ce jour-là."""
    en_rupture = panel.loc[panel["en_rupture"], ["id_station", "jour"]].rename(columns={"id_station": "id_voisine"})
    compte = (
        paires.merge(en_rupture, on="id_voisine")
        .groupby(["id_station", "jour"])
        .size()
        .rename("nb_voisines_en_rupture")
        .reset_index()
    )
    nb_voisines = paires.groupby("id_station").size().rename("nb_voisines").reset_index()

    panel = panel.merge(compte, on=["id_station", "jour"], how="left")
    panel = panel.merge(nb_voisines, on="id_station", how="left")
    colonnes = ["nb_voisines_en_rupture", "nb_voisines"]
    panel[colonnes] = panel[colonnes].fillna(0).astype(int)
    return panel