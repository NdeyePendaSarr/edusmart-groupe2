
# Répartition des tâches - Projet EduSmart Decision Platform

## Membres du groupe

| Membre | Source | Technologie | Responsabilité |
|---|---|---|---|
| Aissata Diallo | Gestion académique | PostgreSQL | Création, génération, extraction PostgreSQL |
| Ndeye Penda Sarr | Plateforme pédagogique | MySQL | Création, génération, extraction MySQL |
| Bachir Deme | Ressources Humaines | CSV | Génération et extraction des fichiers CSV |
| Mouhameth Diop | Journaux application mobile | MongoDB | Génération et extraction des documents MongoDB |
| Seydine Wade | Plateforme temps réel | Redis | Génération et extraction des données Redis |

---

# Travail demandé pour chaque source

Chaque membre doit réaliser :

## 1. Création de la source

- Création de la structure ;
- Définition des champs ;
- Définition des contraintes ;
- Documentation.

## 2. Génération des données

Les données sont générées automatiquement avec :

- Python ;
- Faker ;
- random ;
- uuid ;
- datetime.

## 3. Injection d'anomalies

Chaque source doit contenir volontairement :

- valeurs manquantes ;
- doublons ;
- erreurs de format ;
- incohérences métier ;
- données non standardisées.

## 4. Extraction

Chaque source doit fournir un script :

- extract_postgresql.py ;
- extract_mysql.py ;
- extract_csv.py ;
- extract_mongodb.py ;
- extract_redis.py.

Ces scripts alimenteront ensuite le processus ETL global.

---

# Organisation Git

Branche principale :

main

Branche développement :

dev

Chaque membre travaille sur une branche personnelle :

- feature/postgresql-aissata
- feature/mysql-penda
- feature/csv-bachir
- feature/mongodb-mouhameth
- feature/redis-seydine

Les modifications sont intégrées dans dev puis fusionnées dans main.
