import csv
import io
import json
import zipfile
from pathlib import Path

"""Téléchargement des départements et des populations INSEE 2022."""

import urllib.request

URL_GEO = (
    "https://raw.githubusercontent.com/gregoiredavid/"
    "france-geojson/master/departements-version-simplifiee.geojson"
)

URL_INSEE = (
    "https://www.insee.fr/fr/statistiques/fichier/"
    "8290591/ensemble.zip"
)


def preparer_geographie():
    """Prépare les contours et populations des départements métropolitains."""

    dossier_brut = Path("data/brut")
    dossier_traite = Path("data/traite")
    dossier_brut.mkdir(parents=True, exist_ok=True)
    dossier_traite.mkdir(parents=True, exist_ok=True)

    # 1. Télécharger les contours des départements
    fichier_geo = dossier_brut / "departements.geojson"

    if not fichier_geo.exists():
        urllib.request.urlretrieve(URL_GEO, fichier_geo)

    with open(fichier_geo, encoding="utf-8") as f:
        geo = json.load(f)

    codes = {x["properties"]["code"] for x in geo["features"]}

    if len(codes) != 96:
        raise ValueError("Le GeoJSON doit contenir 96 départements.")

    # 2. Télécharger les populations INSEE
    fichier_zip = dossier_brut / "populations_2022.zip"

    if not fichier_zip.exists():
        urllib.request.urlretrieve(URL_INSEE, fichier_zip)

    with zipfile.ZipFile(fichier_zip) as z:
        contenu = z.read("donnees_departements.csv").decode("utf-8-sig")

    lecteur = csv.DictReader(io.StringIO(contenu), delimiter=";")

    populations = []
    for ligne in lecteur:
        if ligne["DEP"] in codes:
            populations.append({
                "departement": ligne["DEP"],
                "nom": ligne["Département"],
                "population": int(ligne["PMUN"])
            })

    # 3. Contrôler la cohérence
    if len(populations) != 96:
        raise ValueError("Il manque des départements dans les populations.")

    if len({x["departement"] for x in populations}) != 96:
        raise ValueError("Certains départements sont en double.")

    # 4. Enregistrer le résultat
    fichier_sortie = dossier_traite / "populations_2022.csv"

    with open(fichier_sortie, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["departement", "nom", "population"]
        )
        writer.writeheader()
        writer.writerows(populations)

    print("96 départements vérifiés.")
    print("Population totale :", sum(x["population"] for x in populations))
    print("Fichiers géographiques prêts.")


def verifier_departements_stations(df_stations):
    """Compare les départements déclarés aux positions GPS des stations."""
    import geopandas as gpd

    url = (
        "https://raw.githubusercontent.com/gregoiredavid/"
        "france-geojson/master/departements.geojson"
    )

    # Récupération des contours détaillés
    with urllib.request.urlopen(url, timeout=60) as reponse:
        geo = json.load(reponse)

    departements = gpd.GeoDataFrame.from_features(
        geo["features"], crs="EPSG:4326"
    )[["code", "geometry"]]

    # Conversion des stations en points géographiques
    stations_geo = gpd.GeoDataFrame(
        df_stations.copy(),
        geometry=gpd.points_from_xy(
            df_stations["longitude"],
            df_stations["latitude"]
        ),
        crs="EPSG:4326"
    )

    # Attribution géographique indépendante
    resultat = gpd.sjoin(
        stations_geo,
        departements,
        how="left",
        predicate="within"
    )

    if len(resultat) != len(df_stations):
        raise ValueError("La jointure a modifié le nombre de stations.")

    hors_contours = resultat["code"].isna()
    departement_different = (
        ~hors_contours
        & (resultat["departement"] != resultat["code"])
    )

    anomalies = resultat.loc[
        hors_contours | departement_different
    ].copy()

    print("Stations analysées :", len(df_stations))
    print("Stations hors contours :", hors_contours.sum())
    print("Départements différents :", departement_different.sum())
    print("Total des anomalies :", len(anomalies))

    return anomalies



if __name__ == "__main__":
    preparer_geographie()