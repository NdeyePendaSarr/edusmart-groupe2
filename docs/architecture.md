# Architecture du projet EduSmart Decision Platform

## 1. Présentation

EduSmart est une plateforme de formation en ligne utilisant plusieurs systèmes sources indépendants.

L'objectif est de construire une plateforme décisionnelle permettant de centraliser les données issues de différentes technologies afin de produire des analyses et des tableaux de bord.

---

# 2. Architecture générale

```
                 SOURCES DE DONNÉES

 PostgreSQL        MySQL        CSV
 Académique      Learning       RH

 MongoDB                       Redis
 Mobile                         Temps réel


                    |
                    |
                    v

                    ETL

          Extraction des données

          Transformation :
          - nettoyage
          - standardisation
          - contrôle qualité

          Chargement


                    |
                    v

             DATA WAREHOUSE


                    |
                    v

          TABLEAUX DE BORD BI
```

---

# 3. Sources de données

## PostgreSQL

Base :
edusmart_academic

Domaine :
Gestion académique

Contenu :

* étudiants
* filières
* classes
* inscriptions
* paiements

## MySQL

Base :
edusmart_learning

Domaine :
Plateforme pédagogique

Contenu :

* modules
* cours
* quiz
* notes
* progression
* temps de connexion

## CSV

Domaine :
Ressources humaines

Fichiers :

* enseignants.csv
* departements.csv
* salaires.csv
* absences.csv

## MongoDB

Collection :

events

Domaine :

Journaux de l'application mobile.

Contient :

* connexions
* consultations
* quiz
* actions utilisateurs

## Redis

Domaine :

Données temps réel.

Contient :

* sessions actives
* progression rapide
* notifications
* classements

---

# 4. Pipeline décisionnel

Sources opérationnelles

↓

Extraction

↓

Zone de staging

↓

Nettoyage et transformation

↓

Data Warehouse

↓

Analyse et visualisation

---

# 5. Technologies utilisées

| Domaine                       | Technologie  |
| ----------------------------- | ------------ |
| Base relationnelle académique | PostgreSQL   |
| Plateforme pédagogique        | MySQL        |
| Fichiers RH                   | CSV          |
| Documents événements          | MongoDB      |
| Temps réel                    | Redis        |
| ETL                           | Python       |
| Data Warehouse                | SQL          |
| Visualisation                 | BI Dashboard |
