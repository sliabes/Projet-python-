"""Téléchargement et lecture du flux annuel des prix et ruptures de carburants."""

import io
import zipfile
from pathlib import Path

import pandas as pd
import requests
from lxml import etree

URL_FLUX_ANNUEL = "https://donnees.roulez-eco.fr/opendata/annee/{annee}"


def telecharger_flux_annuel(annee: int, dossier: str = "data/brut") -> Path:
    """Télécharge le zip du flux annuel et en extrait le XML. Renvoie le chemin du XML."""
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    deja_la = list(dossier.glob("*.xml"))
    if deja_la:
        return deja_la[0]
    reponse = requests.get(URL_FLUX_ANNUEL.format(annee=annee), timeout=300)
    reponse.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(reponse.content)) as archive:
        nom_xml = archive.namelist()[0]
        archive.extract(nom_xml, dossier)
    return dossier / nom_xml


def lire_ruptures(chemin_xml: Path) -> pd.DataFrame:
    """Parcourt le XML station par station et renvoie une ligne par rupture."""
    lignes = []
    for _, station in etree.iterparse(str(chemin_xml), tag="pdv"):
        for rupture in station.findall("rupture"):
            lignes.append({
                "id_station": station.get("id"),
                "latitude": station.get("latitude"),
                "longitude": station.get("longitude"),
                "code_postal": station.get("cp"),
                "type_route": station.get("pop"),
                "carburant": rupture.get("nom") or rupture.get("fuel"),
                "debut": rupture.get("debut"),
                "fin": rupture.get("fin"),
            })
        station.clear()  # libère la mémoire : le fichier est volumineux
    df_ruptures = pd.DataFrame(lignes)
    df_ruptures["debut"] = pd.to_datetime(df_ruptures["debut"], errors="coerce")
    df_ruptures["fin"] = pd.to_datetime(df_ruptures["fin"], errors="coerce")
    return df_ruptures


def lire_stations(
    chemin_xml: Path,
    date_debut: str = "2022-09-01",
    date_fin: str = "2022-11-30",
) -> pd.DataFrame:
    """Renvoie une ligne par station, avec son nombre de mises à jour de prix sur la période.

    Une station qui n'a déclaré aucun prix pendant la période est probablement fermée :
    ce compteur permet de ne garder que les stations actives pour le calcul des pourcentages.
    """
    lignes = []
    for _, station in etree.iterparse(str(chemin_xml), tag="pdv"):
        nb_maj_periode = sum(
            1
            for prix in station.findall("prix")
            if date_debut <= (prix.get("maj") or "")[:10] <= date_fin
        )
        lignes.append({
            "id_station": station.get("id"),
            "latitude": station.get("latitude"),
            "longitude": station.get("longitude"),
            "code_postal": station.get("cp"),
            "type_route": station.get("pop"),
            "nb_maj_periode": nb_maj_periode,
        })
        station.clear()
    return pd.DataFrame(lignes)