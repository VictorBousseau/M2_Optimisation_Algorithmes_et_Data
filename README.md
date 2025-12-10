# Optimisation, Algorithmes et Data (M2)

Ce dépôt contient l'ensemble des travaux réalisés dans le cadre du cours "Optimisation, Algorithmes et Data". Il regroupe divers exercices pratiques ainsi qu'un projet final basé sur un challenge Google Hashcode.

## Contenu du Dépôt

### 1. Exercices et Cours
Le dossier `Exercices` contient une série de Travaux Dirigés (TD) et d'exercices couvrant les thématiques du cours. Ces exercices (Exo_3 à Exo_10) explorent différents aspects de l'optimisation et de l'algorithmique.

### 2. Projet : Google Hashcode 2017 - Streaming Videos
Le projet principal, situé dans le dossier `ProjetOptimisation`, porte sur la résolution du problème "Streaming Videos" proposé lors du Google Hashcode 2017.

#### Description du Problème
L'objectif est d'optimiser la mise en cache de vidéos pour minimiser le temps de latence des requêtes utilisateurs. Nous disposons de :
- Un ensemble de vidéos de différentes tailles.
- Des serveurs de cache avec une capacité limitée.
- Des "endpoints" (points d'accès) reliés au datacenter principal et à plusieurs caches.
- Des requêtes utilisateurs demandant des vidéos spécifiques depuis des endpoints donnés.

Le but est de décider quelles vidéos placer dans quels serveurs de cache pour maximiser le gain total (latence économisée).

#### Approche Technique
La solution implémentée dans `videos.py` utilise une approche hybride :

1.  **Solution Initiale (Heuristique Gloutonne)** :
    *   Calcul d'un score de densité pour chaque paire (cache, vidéo) basé sur le gain potentiel divisé par la taille de la vidéo.
    *   Remplissage des caches avec les éléments les plus "rentables" jusqu'à saturation pour obtenir une solution de départ réalisable.

2.  **Optimisation Exacte (PLNE avec Gurobi)** :
    *   Modélisation du problème sous forme de Programme Linéaire en Nombres Entiers (MIP).
    *   **Variables** : Variables binaires $y_{c,v}$ (vidéo $v$ dans cache $c$) et $x_{r,c}$ (requête $r$ servie par cache $c$).
    *   **Contraintes** : Respect de la capacité des caches, unicité de la source pour chaque requête (ou aucune).
    *   **Objectif** : Maximiser la somme des gains de latence.
    *   Utilisation du solveur **Gurobi** pour améliorer la solution initiale.

#### Utilisation
Pour exécuter le script :
```bash
python videos.py [fichier_entree.in]
```
Le script génère un fichier `.out` contenant la configuration des caches et, si possible, un fichier `.mps` pour le modèle.

> **Note** : Les fichiers de données volumineux (`.mps`, `.zip`) sont exclus du dépôt pour respecter les limites de taille.
