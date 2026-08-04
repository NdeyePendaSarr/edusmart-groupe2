# Dictionnaire de données - EduSmart Decision Platform

## 1. Objectif

Ce document décrit les principales données utilisées dans le projet EduSmart Decision Platform.

Il permet de définir :

* les sources de données ;
* les attributs importants ;
* les identifiants utilisés ;
* les correspondances entre les systèmes sources ;
* les règles nécessaires à l'intégration dans le Data Warehouse.

---

# 2. Sources de données

## Source 1 - PostgreSQL : Gestion académique

### Base

`edusmart_academic`

### Responsable

Aissata Diallo

### Tables principales

| Table        | Description                             |
| ------------ | --------------------------------------- |
| etudiants    | Informations personnelles des étudiants |
| filieres     | Formations proposées                    |
| classes      | Classes associées aux filières          |
| inscriptions | Inscription des étudiants               |
| paiements    | Historique des paiements                |

---

## Identifiant étudiant

Dans PostgreSQL :

Table :

`etudiants`

Clé primaire :

```
id_etudiant
```

Type :

```
UUID
```

Identifiant métier :

```
matricule
```

Exemple :

```
ETU-2026-00145
```

---

# Source 2 - MySQL : Plateforme pédagogique

## Base

`edusmart_learning`

### Responsable

Ndeye Penda Sarr

### Tables principales

| Table           | Description                |
| --------------- | -------------------------- |
| modules         | Modules de formation       |
| cours           | Cours associés aux modules |
| quiz            | Quiz des cours             |
| notes           | Résultats des étudiants    |
| progression     | Avancement pédagogique     |
| temps_connexion | Historique des connexions  |

---

## Identifiant étudiant

Contrairement à PostgreSQL, MySQL n'utilise pas directement :

```
id_etudiant
```

La plateforme LMS utilise :

```
student_code
```

Format :

```
LMS-XXXXX
```

Exemple :

```
LMS-000154
```

Cet identifiant sera utilisé pour faire le rapprochement avec MongoDB et Redis.

---

# Source 3 - CSV : Ressources Humaines

## Responsable

Bachir Deme

## Fichiers

| Fichier          | Description              |
| ---------------- | ------------------------ |
| enseignants.csv  | Informations enseignants |
| departements.csv | Départements             |
| salaires.csv     | Historique salaires      |
| absences.csv     | Absences enseignants     |

---

## Identifiant enseignant

Identifiant RH :

```
teacher_code
```

Exemple :

```
TCH-00125
```

Cet identifiant sera utilisé dans les dimensions RH du Data Warehouse.

---

# Source 4 - MongoDB : Application mobile

## Base

`edusmart_mobile`

Collection :

```
events
```

## Responsable

Mouhameth Diop

MongoDB contient les événements utilisateurs sous forme de documents JSON.

---

## Identifiant étudiant

Champ :

```
student_code
```

Format :

```
LMS-XXXXX
```

Exemple :

```
LMS-000154
```

Correspondance :

```
MongoDB.student_code
        =
MySQL.student_code
```

---

# Source 5 - Redis : Temps réel

## Responsable

Seydine Wade

Redis contient les données temporaires de la plateforme.

---

## Structures principales

### Sessions

Clé :

```
session:{session_id}
```

Informations :

* student_code
* status
* login_time
* last_activity

### Progression

Clé :

```
progress:{student_code}
```

---

### Classement

Clé :

```
leaderboard:python
```

---

# 3. Gestion des identifiants communs

## Problème

Chaque système possède sa propre manière d'identifier un étudiant.

| Source     | Identifiant      |
| ---------- | ---------------- |
| PostgreSQL | id_etudiant UUID |
| MySQL      | student_code     |
| MongoDB    | student_code     |
| Redis      | student_code     |

---

# 4. Stratégie d'intégration

Pour éviter les conflits entre les systèmes, le Data Warehouse utilisera ses propres clés techniques.

Exemple :

## Dimension étudiant

Table :

```
dim_etudiant
```

Structure :

| Champ              | Description          |
| ------------------ | -------------------- |
| student_key        | Clé technique DW     |
| id_etudiant_source | UUID PostgreSQL      |
| student_code       | Identifiant LMS      |
| matricule          | Matricule académique |
| nom                | Nom                  |
| prenom             | Prénom               |
| sexe               | Sexe                 |
| ville              | Ville                |
| pays               | Pays                 |

---

# 5. Correspondances principales

## Étudiant

```
PostgreSQL
id_etudiant
      |
      |
      v

dim_etudiant.student_key

      ^
      |
      |

MySQL
student_code

MongoDB
student_code

Redis
student_code
```

---

## Formation

Sources :

PostgreSQL :

```
filieres
```

MySQL :

```
modules
cours
```

MongoDB :

```
module_code
course_code
```

Une table de correspondance sera nécessaire lors de l'intégration.

---

## Temps

Toutes les sources utilisent des dates différentes :

Exemples :

PostgreSQL :

```
DATE
```

MySQL :

```
TIMESTAMP
```

MongoDB :

```
DateTime ISO
```

Redis :

```
chaine texte
```

Une dimension temps sera créée :

```
dim_date
```

---

# 6. Règles de qualité des données

Avant chargement dans le Data Warehouse :

## Nettoyage

* suppression des doublons ;
* correction des formats ;
* traitement des valeurs manquantes ;
* standardisation des catégories.

## Contrôle

Vérification :

* clés étrangères ;
* formats de dates ;
* valeurs numériques ;
* cohérence métier.

---

# 7. Modèle décisionnel prévu

Le Data Warehouse contiendra :

## Dimensions

* dim_etudiant
* dim_date
* dim_formation
* dim_enseignant
* dim_cours

## Tables de faits

* fact_inscriptions
* fact_paiements
* fact_notes
* fact_connexions
* fact_evenements_mobile

---

# Conclusion

Le dictionnaire de données sert de référence commune pour toute l'équipe.

Il garantit que les cinq sources hétérogènes pourront être intégrées dans une plateforme décisionnelle unique.
