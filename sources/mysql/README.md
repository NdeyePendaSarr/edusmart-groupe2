# Source 2 - MySQL : Plateforme pédagogique

## Responsable

Ndeye Penda Sarr

## Base de données

edusmart_learning

## Description

Cette source représente la plateforme d'apprentissage en ligne EduSmart.

Elle contient les informations relatives :

- aux modules ;
- aux cours ;
- aux quiz ;
- aux résultats des étudiants ;
- à la progression ;
- aux temps de connexion.

## Technologie

- MySQL
- Python
- Faker

## Structure prévue

Tables :

- modules
- cours
- quiz
- notes
- progression
- temps_connexion

## Génération des données

Le script :

generate_data.py

permet de générer automatiquement les données avec :

- Faker ;
- random ;
- uuid ;
- datetime.

## Anomalies introduites

Les données contiennent volontairement :

- catégories différentes (Data, DATA, Data Science) ;
- progressions supérieures à 100% ;
- valeurs négatives ;
- connexions incomplètes ;
- appareils avec plusieurs formats.

## Extraction

Le fichier :

extract_mysql.py

permettra d'extraire les données MySQL vers le processus ETL.