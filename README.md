# Les pénuries de carburant se propagent-elles comme une épidémie ?

**Projet Python pour la data science — ENSAE Paris, 2026**
**Auteurs :** Sarah Liabes et Adam Trabelsi

## 1. Problématique

À l'automne 2022, des grèves dans les raffineries et dépôts de TotalEnergies et d'Esso-ExxonMobil provoquent de fortes difficultés d'approvisionnement dans les stations-service françaises. Nous cherchons à comprendre comment cette pénurie s'est diffusée, en distinguant deux mécanismes :

- **H1 — Choc logistique commun :** les ruptures résultent de l'arrêt des raffineries et dépôts, qui touche simultanément de nombreux territoires, et d'abord ceux qui sont proches des sites en grève.
- **H2 — Contagion locale :** quand une station est à sec, ses clients se reportent sur les stations voisines, qui se vident à leur tour, comme une épidémie qui se transmet de proche en proche.

Nous comparons enfin la forme de la crise à celle d'une vraie épidémie : les deux premières vagues de COVID-19 en France, en 2020.

## 2. Résultats principaux

- **La crise suit le calendrier des grèves.** La part de stations en rupture passe d'environ 6 % en septembre à **49,6 % le 16 octobre** ; les nouvelles ruptures culminent le 10 octobre (857 stations).
- **Les départements basculent presque en même temps.** Parmi les 84 départements qui atteignent 20 % de stations en rupture, la moitié le font entre le 3 et le 8 octobre.
- **Les départements éloignés des sites en grève sont touchés plus tard** (corrélation de Spearman ρ = 0,39 sur 82 départements) : un argument pour H1.
- **La contagion locale existe, mais elle est secondaire.** Une station dont les voisines sont en rupture tombe deux fois plus souvent en rupture, mais l'essentiel de cet écart s'explique par la situation de son département ; l'effet restant n'apparaît que lorsque la majorité des voisines sont à sec.
- **La crise n'a pas la forme d'une épidémie.** Elle monte en 7 jours (de la moitié de son pic au pic), contre 11 à 19 jours pour les vagues de COVID-19.

**Conclusion :** les données suggèrent un choc logistique commun, amplifié localement par le report des automobilistes lorsque l'offre devient très rare, plutôt qu'une propagation de type épidémique. Ces résultats sont descriptifs et n'établissent pas de causalité.

## 3. Sources des données

| Donnée | Source | Utilisation |
|---|---|---|
| Stations-service et épisodes de rupture, 2022 | Flux annuel de [prix-carburants.gouv.fr](https://www.prix-carburants.gouv.fr/rubrique/opendata/) (ministère de l'Économie), téléchargé par le code | Toutes les analyses |
| Raffineries et dépôts en grève (7 sites, dates de grève) | Table construite à la main à partir d'articles de presse, une source par ligne : `data/manuel/raffineries_depots.csv` | H1 |
| Part de stations en difficulté publiée pendant la crise | Ministère de la Transition énergétique, via la presse : `data/manuel/chiffres_ministere.csv` | Validation (G0) |
| Contours des départements | [france-geojson](https://github.com/gregoiredavid/france-geojson), téléchargé par le code | Cartes (G3) |
| Nouvelles hospitalisations pour COVID-19 par département | Santé publique France, données SI-VIC sur [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/), téléchargé par le code | Comparaison (G8) |

## 4. Méthode

1. **Collecte et nettoyage** (`collecte.py`, `nettoyage.py`) : 9 563 stations actives de France métropolitaine, ruptures des quatre carburants principaux (gazole, SP95, SP95-E10, SP98) en cours entre septembre et novembre 2022, d'une durée de 1 heure à 30 jours (106 527 ruptures).
2. **Panel station × jour** (`indicateurs.py`) : chaque jour à 13 h, heure des relevés du ministère, nous notons si chaque station a une rupture en cours. Nous en tirons la prévalence, l'incidence et la date de décollage de chaque département.
3. **H1** (`distances.py`) : distance de chaque département au site en grève le plus proche, comparée à sa date de décollage.
4. **H2** (`indicateurs.py`, `contagion.py`) : probabilité de tomber en rupture selon que les stations voisines (moins de 5 km) l'étaient la veille, à département et jour fixés.
5. **Comparaison COVID** (`covid.py`) : courbes lissées sur 7 jours, alignées sur leur pic, temps de montée et de descente.

## 5. Organisation du dépôt

- `main.ipynb` : le rapport, avec le code, les graphiques et leur interprétation.
- `src/penuries/` : les modules Python (`collecte`, `nettoyage`, `indicateurs`, `distances`, `geographie`, `contagion`, `covid`, `visualisation`).
- `data/manuel/` : les deux tables construites à la main, seules données versionnées.
- `data/brut/`, `data/propre/` : données téléchargées et nettoyées, créées par le notebook et non versionnées.
- `resultats/` : figures et tableaux exportés par le notebook (G3, G4).
- `annexes/verification_stations.ipynb` : vérifications complémentaires des coordonnées des stations.

## 6. Reproduire les résultats

```bash
git clone https://github.com/sliabes/Projet-python-.git
cd Projet-python-
pip install -r requirements.txt
```

Ouvrir ensuite `main.ipynb` et exécuter toutes les cellules (**Run All**). Le notebook télécharge lui-même les données ; une connexion Internet est nécessaire, et la première exécution prend quelques minutes.

En cas de conflit de versions (par exemple avec l'environnement `base` d'Anaconda), créer un environnement dédié :

```bash
conda create -n penuries -c conda-forge python=3.11 geopandas -y
conda activate penuries
pip install -r requirements.txt
```

## 7. Limites

- Les ruptures reposent sur les déclarations des stations, parfois tardives : notre indicateur surestime le niveau de la pénurie par rapport aux chiffres officiels (de 5 à 21 points), surtout en fin de crise, mais en restitue bien la chronologie.
- La distance à vol d'oiseau ne reflète pas les circuits réels de livraison.
- L'enseigne des stations n'est pas disponible, alors que la remise de TotalEnergies a pu concentrer la demande sur ses stations.
- Les analyses sont descriptives : elles décrivent des associations, sans établir de lien de causalité.