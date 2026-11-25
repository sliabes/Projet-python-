# Les pénuries de carburant se propagent-elles comme une épidémie ?

**Projet Python pour la data science — ENSAE Paris, 2026**

**Équipe actuelle :** Sarah Liabes et Adam Trabelsi.

## 1. Problématique

En octobre 2022, les grèves dans les raffineries et dépôts pétroliers ont provoqué d'importantes difficultés d'approvisionnement dans les stations-service françaises.

Notre projet cherche à comprendre la dynamique temporelle et géographique de cette crise, en distinguant deux mécanismes :

- **H1 — Choc logistique commun :** les pénuries résultent principalement de perturbations des infrastructures pétrolières, qui touchent simultanément plusieurs territoires.
- **H2 — Contagion locale :** les difficultés d'une station conduisent les automobilistes à se reporter sur les stations voisines, favorisant une propagation de proche en proche.

Nous comparons également cette dynamique à celle d'une véritable épidémie, la première vague de COVID-19.

## 2. Sources des données

- **Prix-carburants.gouv.fr :** flux annuel 2022 des stations-service et des épisodes de rupture.
- **Ministère de la Transition énergétique et articles de presse :** chiffres officiels de stations en difficulté, regroupés dans `data/manuel/chiffres_ministere.csv`.
- **Presse économique et généraliste :** localisation et calendrier des grèves des raffineries et dépôts, avec les sources documentées dans `data/manuel/raffineries_depots.csv`.
- **INSEE :** populations départementales.
- **France-GeoJSON :** contours géographiques des départements français.

Les données relatives aux épisodes de rupture sont téléchargées et traitées par les fonctions Python du projet.

## 3. Méthodologie

L'analyse porte sur la période de septembre à novembre 2022 et sur 9 563 stations-service actives de France métropolitaine.

Pour chaque station et chaque journée, nous déterminons si au moins un carburant est déclaré indisponible lors du relevé à 13 h.

Nous construisons ensuite plusieurs indicateurs :

- La prévalence quotidienne des ruptures.
- Le nombre de nouvelles stations entrant en rupture.
- La prévalence départementale.
- Les dates de décollage des pénuries par département.
- La distance géographique aux sites pétroliers en grève.

Les analyses H1 reposent notamment sur des cartes départementales (G3) et sur l'association entre distance aux sites actifs en grève et date de décollage des pénuries (G4).

L'analyse H2 étudie la possibilité d'une transmission locale des ruptures entre stations voisines.

## 4. Organisation du dépôt

- `main.ipynb` : notebook principal regroupant le rapport, les analyses et les visualisations.
- `src/penuries/` : modules Python de collecte, nettoyage, calcul des indicateurs, géographie, distances et visualisation.
- `data/brut/` : données brutes téléchargées.
- `data/manuel/` : données complémentaires construites et documentées manuellement.
- `data/traite/` : données intermédiaires ou traitées.
- `resultats/` : graphiques et tableaux exportés.
- `annexes/` : vérifications et analyses complémentaires.
- `requirements.txt` : dépendances Python du projet.

## 5. Reproduction des analyses

Le projet est accessible à l'adresse :

https://github.com/sliabes/Projet-python-

Cloner le dépôt :

`git clone https://github.com/sliabes/Projet-python-.git`

Se placer dans le projet :

`cd Projet-python-`

Installer les dépendances :

`pip install -r requirements.txt`

Ouvrir ensuite `main.ipynb` dans JupyterLab ou VS Code, sélectionner un environnement Python disposant des dépendances et exécuter toutes les cellules dans l'ordre (**Run All**).

Une connexion Internet peut être nécessaire au téléchargement initial des données et des contours géographiques.

## 6. Limites méthodologiques

Les analyses sont principalement descriptives et ne permettent pas d'établir un lien de causalité.

La distance à un site pétrolier en grève ne représente pas nécessairement la distance réelle d'approvisionnement d'une station.

Les données de rupture reposent sur des déclarations dont les dates et la précision peuvent varier.

Enfin, notre indicateur de rupture ne correspond pas exactement à la définition utilisée pour les statistiques officielles. La comparaison G0 fait apparaître des écarts de niveau importants, qui imposent une interprétation prudente.

Les résultats doivent donc être considérés comme des éléments permettant de discuter les hypothèses H1 et H2, et non comme des preuves définitives.