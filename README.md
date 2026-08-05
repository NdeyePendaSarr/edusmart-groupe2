# EduSmart Decision Platform

## 1. Présentation du projet

EduSmart est une plateforme de formation en ligne qui possède plusieurs applications métiers développées indépendamment.

Chaque application possède son propre système de stockage :

- PostgreSQL : Gestion académique
- MySQL : Plateforme pédagogique
- CSV : Ressources Humaines
- MongoDB : Journaux de l'application mobile
- Redis : Données temps réel

L'objectif du projet est de construire une **plateforme décisionnelle unique** permettant au Directeur Général d'analyser l'ensemble des activités de l'entreprise.

La solution mise en place suit une architecture décisionnelle basée sur un processus **ETL (Extract - Transform - Load)** :

1. Extraction des données provenant de plusieurs sources.
2. Nettoyage et transformation des données.
3. Contrôle de qualité.
4. Intégration dans un Data Warehouse.
5. Exploitation via des tableaux de bord décisionnels.


---

# 2. Objectifs du projet

Les objectifs principaux sont :

- Centraliser les données provenant de plusieurs systèmes.
- Manipuler différents types de bases de données.
- Mettre en place un processus ETL complet.
- Comprendre les problématiques réelles de qualité des données.
- Nettoyer les anomalies présentes dans les sources.
- Construire un modèle décisionnel.
- Préparer les données pour l'analyse.


---

# 3. Architecture générale

L'architecture du projet est organisée autour de trois grandes parties :

```
                 SOURCES DE DONNEES

 PostgreSQL      MySQL       CSV       MongoDB       Redis
     |             |           |            |            |
     ---------------------------------------------------
                          |
                          |
                         ETL

              Extraction
                   |
              Transformation
                   |
              Contrôle qualité
                   |
              Chargement


                    DATA WAREHOUSE

              Dimensions + Faits


                    ANALYSE

              Tableaux de bord BI

```


---

# 4. Sources de données

## Source 1 : PostgreSQL - Gestion académique

Base :

```
edusmart_academic
```

Responsable :

```
Aissata Diallo
```

Contient :

- étudiants
- filières
- classes
- inscriptions
- paiements


Dossier :

```
sources/postgresql
```


Fichiers principaux :

```
create_database.sql
generate_data.py
insert_data.py
extract_postgresql.py
README.md
```


---

## Source 2 : MySQL - Plateforme pédagogique

Base :

```
edusmart_learning
```

Responsable :

```
Ndeye Penda Sarr
```


Contient :

- modules
- cours
- quiz
- notes
- progression
- temps de connexion


Dossier :

```
sources/mysql
```


Fichiers principaux :

```
create_database.sql
generate_data.py
insert_data.py
extract_mysql.py
README.md
```


---

## Source 3 : CSV - Ressources Humaines

Responsable :

```
Bachir Deme
```


Fichiers :

```
enseignants.csv
departements.csv
salaires.csv
absences.csv
```


Dossier :

```
sources/csv
```


Les fichiers contiennent :

- enseignants
- départements
- salaires
- absences


---

## Source 4 : MongoDB - Journaux application mobile

Responsable :

```
Mouhameth Diop
```


Base :

```
EduSmart Mobile Logs
```


Collection :

```
events
```


Contient :

- connexions utilisateurs
- ouvertures de cours
- quiz
- téléchargements
- actions mobiles


Dossier :

```
sources/mongodb
```


Fichiers :

```
create_database.py
generate_data.py
insert_data.py
extract_mongodb.py
README.md
```


---

## Source 5 : Redis - Plateforme temps réel

Responsable :

```
Seydina Wade
```


Redis stocke :

- sessions utilisateurs
- progression temporaire
- derniers cours consultés
- notifications
- classement étudiants


Dossier :

```
sources/redis
```


Fichiers :

```
create_source.py
generate_data.py
insert_data.py
extract_redis.py
README.md
```


---

# 5. Organisation du dépôt

Structure actuelle :

```
edusmart-groupe2

│
├── sources
│   │
│   ├── postgresql
│   ├── mysql
│   ├── csv
│   ├── mongodb
│   └── redis
│
│
├── etl
│   │
│   ├── extraction
│   │       └── extract_all.py
│   │
│   ├── transformation
│   │       ├── cleaning.py
│   │       ├── standardisation.py
│   │       └── quality_checks.py
│   │
│   └── loading
│           └── load_dw.py
│
│
├── warehouse
│   │
│   ├── create_dw.sql
│   ├── dimensions.sql
│   ├── facts.sql
│   └── star_schema.sql
│
│
├── docs
│   │
│   ├── architecture.md
│   ├── dictionnaire_donnees.md
│   └── repartition_taches.md
│
│
├── requirements.txt
├── docker-compose.yml
├── CONTRIBUTING.md
└── README.md

```


---

# 6. Technologies utilisées


## Bases de données

| Technologie | Utilisation |
|---|---|
| PostgreSQL | Gestion académique |
| MySQL | Plateforme pédagogique |
| MongoDB | Logs mobiles JSON |
| Redis | Temps réel |
| CSV | Ressources RH |


## Langages

- Python
- SQL


## Librairies Python

- Faker : génération des données
- Pandas : manipulation des données
- NumPy : génération aléatoire
- SQLAlchemy : connexion bases SQL
- PyMongo : connexion MongoDB
- Redis-py : connexion Redis


---

# 7. Génération des données

Chaque source possède un générateur permettant de créer des données réalistes avec :

- Faker
- random
- datetime
- uuid


Les données générées contiennent volontairement des anomalies :

- valeurs manquantes
- doublons
- erreurs de saisie
- formats différents
- incohérences métier
- identifiants incompatibles


Ces anomalies permettent de reproduire un environnement réel d'entreprise.


---

# 8. Processus ETL


## Extraction

Les données sont récupérées depuis :

- PostgreSQL
- MySQL
- CSV
- MongoDB
- Redis


Dossier :

```
etl/extraction
```


---

## Transformation

Les traitements réalisés :

- nettoyage
- suppression des doublons
- standardisation des valeurs
- contrôle qualité


Dossier :

```
etl/transformation
```


---

## Chargement

Les données nettoyées sont chargées dans le Data Warehouse.


Dossier :

```
etl/loading
```


---

# 9. Data Warehouse

Le Data Warehouse contient :

## Tables de dimensions

Exemples :

- DimEtudiant
- DimFormation
- DimTemps
- DimEnseignant
- DimCours


## Tables de faits

Exemples :

- FactInscription
- FactPaiement
- FactProgression
- FactConnexion
- FactQuiz


Modèle utilisé :

```
Schéma en étoile (Star Schema)
```


---

# 10. Installation du projet


Cloner le dépôt :

```bash
git clone https://github.com/NdeyePendaSarr/edusmart-groupe2.git
```


Accéder au projet :

```bash
cd edusmart-groupe2
```


Installer les dépendances :

```bash
pip install -r requirements.txt
```


---

# 11. Collaboration Git


Branches utilisées :

```
main
dev

feature/postgresql-aissata
feature/mysql-penda
feature/csv-bachir
feature/mongodb-mouhameth
feature/redis-seydina
```


Workflow :

1. Développer sur sa branche feature.
2. Faire un commit.
3. Pousser la branche.
4. Créer une Pull Request.
5. Fusionner dans dev.


---

# 12. Documentation

Documents disponibles :

```
docs/
```

Contient :

- architecture technique
- dictionnaire des données
- répartition des tâches


---

# 13. Équipe projet


| Membre | Source |
|-|-|
| Aissata Diallo | PostgreSQL |
| Ndeye Penda Sarr | MySQL |
| Bachir Deme | CSV |
| Mouhameth Diop | MongoDB |
| Seydina Wade | Redis |


---

# 14. Etat du projet

Phase actuelle :

✅ Architecture du dépôt créée  
✅ Sources réparties entre membres  
✅ Documentation initiale créée  
✅ Branches Git configurées  
⬜ Génération des données sources  
⬜ Développement ETL  
⬜ Construction Data Warehouse  
⬜ Tableaux de bord décisionnels  


---

# 15. Auteur du projet

Projet réalisé dans le cadre du module :

**Business Intelligence / Data Engineering**

Projet :

**EduSmart Decision Platform**

Année :

2026