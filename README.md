# Projet-python-

# Les pénuries d'essence se propagent-elles comme une épidémie ?

_Auteurs : Sarah Liabes, Adam Trabelsi, Eden Szezot

## Problématique
En octobre 2022, pendant la grève des raffineries, les ruptures de carburant
se sont-elles propagées de proche en proche à partir des raffineries,
ou sont-elles apparues partout en même temps ?

## Données
- Flux annuel 2022 des prix et ruptures de carburants (prix-carburants.gouv.fr)
- Localisation des raffineries et dépôts (Wikipédia)
- Population départementale (INSEE, API Melodi)
- Contours des départements (GeoJSON)

## Reproduction
    git clone https://github.com/<pseudo>/projet-python-.git
    cd projet-python-
    pip install -r requirements.txt
Puis ouvrir `main.ipynb` et lancer **Run All**.

## Structure du dépôt
- `main.ipynb` : rapport principal
- `src/penuries/` : fonctions de collecte, nettoyage, indicateurs et visualisation
- `data/` : données locales (non versionnées)