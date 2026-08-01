# Rapport de projet — Données 2

## 1. Méthode de travail du groupe

Le projet a été mené par une équipe de quatre membres, en s'appuyant sur un dépôt Git partagé (`air-quality-gp18-donnees2`) avec une stratégie de branches `dev en main`. Chaque fonctionnalité était développée sur une branche dédiée puis intégrée via une pull request, permettant une relecture avant fusion dans `main`.

Le travail a été organisé par couche du pipeline de données : extraction, transformation, stockage (warehouse) et orchestration/CI. Cette répartition a permis à chacun de travailler en parallèle sur des modules relativement indépendants, tout en partageant un modèle de données commun défini dès le début du projet (schéma en étoile avec `dim_city`, `dim_time` et `fact_aqi`).

Des points de coordination réguliers ont permis de vérifier la cohérence entre les étapes du pipeline, notamment lors du passage de la donnée brute vers la donnée nettoyée, puis vers l'entrepôt.

## 2. Répartition des tâches

Mihaja : il a fait partie extraction, chargé de la collecte des données brutes depuis l'API Open-Meteo (`fetch_last`, `fetch_history`).

Mayah : elle a fait partie transformation, chargée du nettoyage et de la consolidation du dataset (`build_clean`, `merge_history`).

Koloina : elle a fait partie warehouse, chargée de la conception et de l'implémentation de la couche entrepôt : schéma en étoile, chargement PostgreSQL (`build_warehouse.py`).

Jessy : il a fait partie CI/CD et fiabilisation, chargé de la mise en place de l'automatisation (GitHub Actions) et de la correction des bugs (clés de substitution PostgreSQL, chemins, backfill),et le déploiement.

Cette répartition suit la logique du pipeline ETL : les données extraites par Mihaja alimentent le nettoyage réalisé par Mayah, dont le résultat est chargé dans l'entrepôt construit par Koloina, l'ensemble étant automatisé et fiabilisé par Jessy.

## 3. Difficultés rencontrées et solutions apportées

### 3.1 Choix de l'orchestrateur : d'Airflow à GitHub Actions

Une première approche d'automatisation du pipeline a été explorée avec Apache Airflow (configuration d'un environnement personnalisé et d'un DAG de backfill). Cette solution s'est révélée trop lourde à déployer et à maintenir pour les besoins du projet, notamment en raison de la complexité de configuration de l'environnement Docker associé.

L'équipe a donc fait le choix de migrer vers GitHub Actions, natif au dépôt et beaucoup plus simple à opérer : un workflow planifié (cron horaire) déclenche automatiquement les étapes `fetch_last`, `build_clean` et `build_warehouse`, sans infrastructure supplémentaire à gérer. Les configurations Airflow et Docker obsolètes ont ensuite été retirées du dépôt pour garder une base de code cohérente.

### 3.2 Fiabilisation du chargement en base

Le chargement incrémental des données posait un risque de doublons à chaque exécution du pipeline. Ce problème a été résolu par l'implémentation d'un mécanisme d'upsert PostgreSQL (`ON CONFLICT DO NOTHING`) sur les clés naturelles de chaque dimension, garantissant qu'une donnée déjà présente n'est jamais réinsérée.

### 3.3 Fiabilité du déclenchement planifié

L'équipe a constaté que GitHub Actions ne garantit pas une exécution à l'heure pile pour les workflows planifiés : selon la charge du service, le déclenchement peut être retardé de plusieurs dizaines de minutes, les jobs planifiés étant placés dans une file d'attente partagée entre tous les utilisateurs de la plateforme. Le cron reste configuré pour un déclenchement horaire, mais l'exécution réelle dépend de la disponibilité des runners GitHub. Ce point a été documenté comme une limite connue du système plutôt qu'un dysfonctionnement à corriger.

### 3.4 Chemins et environnements

Plusieurs ajustements ont été nécessaires pour que les scripts fonctionnent de façon identique en local et dans l'environnement d'exécution de GitHub Actions, notamment la résolution des chemins de données relatifs au répertoire racine du projet plutôt qu'au répertoire d'exécution du script.

## 4. Choix techniques justifiés

- **Langage et gestionnaire de paquets :** Python avec `uv`, pour une gestion rapide et reproductible des dépendances, avec un fichier de verrouillage (`uv.lock`) garantissant un environnement identique entre les membres de l'équipe et le pipeline automatisé.
- **Source de données :** l'API Open-Meteo Air Quality, choisie pour sa gratuité, l'absence de clé d'authentification et sa couverture horaire fine sur les cinq villes suivies (Antananarivo, Paris, Tokyo, Sydney, New York).
- **Modélisation :** un schéma en étoile (`dim_city`, `dim_time`, `fact_aqi`) plutôt qu'une table plate, pour séparer clairement les dimensions descriptives des mesures, faciliter les agrégations et limiter la duplication d'information.
- **Base de données :** PostgreSQL hébergé sur Neon, qui offre un hébergement managé gratuit, une mise à l'échelle automatique du calcul et une intégration simple avec SQLAlchemy pour la couche applicative.
- **Orchestration :** GitHub Actions plutôt qu'Airflow, pour les raisons détaillées en section 3.1 — simplicité d'intégration au dépôt existant et absence d'infrastructure à maintenir.
- **Chargement :** un mécanisme d'upsert via SQLAlchemy plutôt que des insertions simples, afin de rendre le pipeline idempotent et rejouable sans risque de doublons.