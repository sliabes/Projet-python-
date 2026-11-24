
"""Calcul des distances géographiques entre stations et raffineries."""

from math import radians, sin, cos, asin, sqrt
import csv


def distance_km(lat1, lon1, lat2, lon2):
    """Calcule la distance à vol d'oiseau entre deux points GPS."""

    # Rayon moyen de la Terre en kilomètres
    R = 6371

    # Conversion des degrés en radians
    lat1, lon1, lat2, lon2 = map(
        radians, [lat1, lon1, lat2, lon2]
    )

    # Formule de Haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    return 2 * R * asin(sqrt(a))


def site_le_plus_proche(lat, lon):
    """Trouve la raffinerie ou le dépôt le plus proche d'un point GPS."""

    fichier = "data/manuel/raffineries_depots.csv"

    with open(fichier, newline="", encoding="utf-8-sig") as f:
        sites = list(csv.DictReader(f))

    distances = []

    for site in sites:
        if not site["latitude"] or not site["longitude"]:
            continue

        d = distance_km(
            lat,
            lon,
            float(site["latitude"]),
            float(site["longitude"])
        )

        distances.append((d, site["site"]))

    if not distances:
        raise ValueError("Aucun site avec des coordonnées GPS.")

    return min(distances)


def calculer_distances_stations(stations):
    """Calcule la distance au site le plus proche pour chaque station."""

    fichier = "data/manuel/raffineries_depots.csv"

    # Charger les sites une seule fois
    with open(fichier, newline="", encoding="utf-8-sig") as f:
        sites = [
            s for s in csv.DictReader(f)
            if s["latitude"] and s["longitude"]
        ]

    if not sites:
        raise ValueError("Aucun site avec des coordonnées GPS.")

    resultats = []

    # Parcourir toutes les stations
    for station in stations:
        lat = float(station["latitude"])
        lon = float(station["longitude"])

        distances = [
            (
                distance_km(
                    lat, lon,
                    float(s["latitude"]),
                    float(s["longitude"])
                ),
                s["site"]
            )
            for s in sites
        ]

        distance, site = min(distances)

        resultats.append({
            "id_station": station["id_station"],
            "site_proche": site,
            "distance_km": round(distance, 2)
        })

    return resultats

if __name__ == "__main__":
    # Test : distance Paris - Marseille
    resultat = distance_km(
        48.8566, 2.3522,
        43.2965, 5.3698
    )

    print("Distance Paris-Marseille :", round(resultat, 2), "km")

    distance, site = site_le_plus_proche(48.8566, 2.3522)

    print("Site le plus proche de Paris :", site)
    print("Distance :", round(distance, 2), "km")

