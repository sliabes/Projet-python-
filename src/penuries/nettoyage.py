"""Nettoyage des stations et des ruptures pour l'étude de la crise d'octobre 2022."""

import pandas as pd

# Définition du ministère : une station est "en difficulté" s'il lui manque l'un de ces carburants
CARBURANTS_PRINCIPAUX = ["Gazole", "SP95", "E10", "SP98"]
DATE_DEBUT = "2022-09-01"
DATE_FIN = "2022-11-30"


def code_departement(code_postal: str) -> str | None:
    """Déduit le code département d'un code postal (Corse : 2A/2B, outre-mer exclu)."""
    if not isinstance(code_postal, str) or len(code_postal) != 5:
        return None
    if code_postal.startswith("97"):
        return None
    if code_postal.startswith("20"):
        return "2A" if int(code_postal) < 20200 else "2B"
    return code_postal[:2]


def nettoyer_stations(df_stations: pd.DataFrame) -> pd.DataFrame:
    """Garde les stations actives de métropole, avec coordonnées en degrés et département."""
    df = df_stations.copy()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce") / 100_000
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce") / 100_000
    df["departement"] = df["code_postal"].apply(code_departement)
    est_active = df["nb_maj_periode"] > 0
    a_une_position = df["latitude"].notna() & df["longitude"].notna()
    return df[est_active & a_une_position & df["departement"].notna()].reset_index(drop=True)


def nettoyer_ruptures(df_ruptures: pd.DataFrame, df_stations_propres: pd.DataFrame) -> pd.DataFrame:
    """Garde les ruptures des carburants principaux, commencées sur la période,
    dans les stations actives, et ajoute leur durée en heures."""
    # Garde aussi les ruptures commencées avant la période mais encore en cours au 1er septembre
    dans_periode = (df_ruptures["debut"] <= DATE_FIN) & (
        df_ruptures["fin"].isna() | (df_ruptures["fin"] >= DATE_DEBUT)
    )
    carburant_principal = df_ruptures["carburant"].isin(CARBURANTS_PRINCIPAUX)
    df = df_ruptures.loc[dans_periode & carburant_principal, ["id_station", "carburant", "debut", "fin"]]

    colonnes_station = ["id_station", "departement", "latitude", "longitude", "type_route"]
    df = df.merge(df_stations_propres[colonnes_station], on="id_station", how="inner")

    df["duree_heures"] = (df["fin"] - df["debut"]).dt.total_seconds() / 3600
    df["fin_connue"] = df["fin"].notna()
    return df.reset_index(drop=True)


def filtrer_durees(
    df_ruptures: pd.DataFrame,
    duree_min_heures: float = 1,
    duree_max_heures: float = 30 * 24,
) -> pd.DataFrame:
    """Écarte les ruptures sans fin, trop courtes (erreurs de déclaration)
    ou trop longues (carburant retiré de la vente)."""
    garde = df_ruptures["fin_connue"] & df_ruptures["duree_heures"].between(
        duree_min_heures, duree_max_heures
    )
    return df_ruptures[garde].reset_index(drop=True)


def exporter_parquet(df: pd.DataFrame, nom_fichier: str, dossier: str = "data/propre") -> str:
    """Enregistre une table propre au format Parquet et renvoie son chemin."""
    from pathlib import Path

    Path(dossier).mkdir(parents=True, exist_ok=True)
    chemin = f"{dossier}/{nom_fichier}"
    df.to_parquet(chemin, index=False)
    return chemin