# Mapping inter-sources : MySQL ↔ PostgreSQL

Ce document explique comment relier les données MySQL (edusmart_learning_v2) aux données PostgreSQL (edusmart_academic, source d'Aissata).

## Contexte

Chaque source EduSmart utilise ses propres identifiants pour les étudiants :

- **PostgreSQL** (Aissata) : matricule au format `ETU` + 5 chiffres (ex : `ETU01001`)
- **MySQL** (Ndeye Penda et équipe MySQL) : `student_code` au format `LMS-` + 5 chiffres (ex : `LMS-01001`)
- **MongoDB** (Mouhameth) : reprend le `student_code` de MySQL
- **Redis** (Seydina) : reprend le `student_code` de MySQL
- **CSV RH** (Bachir) : n'utilise pas de student_code (concerne les enseignants)

## Règle de dérivation

Un `student_code` MySQL peut être dérivé d'un matricule PostgreSQL par :

```python
student_code = "LMS-" + matricule[3:].zfill(5)
```

**Exemples :**
- `ETU01001` → `LMS-01001`
- `ETU12345` → `LMS-12345`

## Analyse quantitative

Sur les données actuellement partagées :

| Population | Volume |
|---|---|
| Matricules totaux dans PostgreSQL | 15 000 (dont 1 495 doublons volontaires) |
| Matricules uniques dans PostgreSQL | 13 505 |
| student_codes dans MySQL | 15 000 |
| **Matches (dans PG et MySQL)** | **12 606** |
| Orphelins MySQL (dans MySQL, pas dans PG) | 2 394 |
| Orphelins PostgreSQL (dans PG, pas dans MySQL) | 899 |

## Catégories d'étudiants pour l'ETL

Le pipeline ETL doit gérer 4 catégories d'étudiants :

### 1. Étudiants complets (12 606)
- Ont un dossier administratif chez Aissata
- Ont une activité pédagogique chez MySQL
- **Cas standard**, les KPI classiques s'appliquent

### 2. Étudiants "actifs sans inscription" (2 394)
- N'ont pas de dossier administratif chez Aissata
- Ont une activité pédagogique chez MySQL
- **Cas particulier** : étudiants "fantômes" du LMS
- Possibles interprétations : étudiants avec accès temporaire, comptes de test, erreurs de saisie
- **Recommandation** : les inclure dans le DW avec un flag `has_admin_record = FALSE`

### 3. Étudiants "inscrits sans activité" (899)
- Ont un dossier administratif chez Aissata
- N'ont aucune activité chez MySQL
- **Cas important** : étudiants inscrits qui n'ont jamais utilisé la plateforme
- **KPI potentiel** : "taux d'engagement post-inscription" = 12 606 / (12 606 + 899) = 93.4%

### 4. Étudiants Aissata avec matricule doublon (ETU1000, 1 495 lignes)
- Le matricule `ETU1000` apparaît 1 496 fois chez Aissata (anomalie A22 de PostgreSQL)
- Se dérive en `LMS-01000` unique côté MySQL
- **Traitement ETL** : déduplication côté PostgreSQL, un seul enregistrement final

## Recommandations pour le Data Warehouse

### Structure de la dimension `dim_etudiant`

```sql
CREATE TABLE dim_etudiant (
    student_key       INTEGER      PRIMARY KEY AUTO_INCREMENT,
    matricule         VARCHAR(20)  NULL,     -- source PostgreSQL
    student_code      VARCHAR(30)  NOT NULL, -- source MySQL/MongoDB/Redis
    nom               VARCHAR(100) NULL,     -- source PostgreSQL
    prenom            VARCHAR(100) NULL,     -- source PostgreSQL
    email             VARCHAR(150) NULL,     -- source PostgreSQL
    ville             VARCHAR(100) NULL,     -- source PostgreSQL
    region            VARCHAR(100) NULL,     -- source PostgreSQL
    has_admin_record  BOOLEAN      NOT NULL,
    has_lms_activity  BOOLEAN      NOT NULL,
    date_creation     TIMESTAMP    NULL
);
```

### Requête de peuplement (esquisse)

```sql
INSERT INTO dim_etudiant (matricule, student_code, nom, prenom, email,
                           ville, region, has_admin_record, has_lms_activity,
                           date_creation)
-- Étudiants complets (match PG + MySQL)
SELECT pg.matricule,
       CONCAT('LMS-', LPAD(SUBSTRING(pg.matricule, 4), 5, '0')) AS student_code,
       pg.nom, pg.prenom, pg.email, pg.ville, pg.region,
       TRUE  AS has_admin_record,
       TRUE  AS has_lms_activity,
       pg.date_creation
FROM staging_postgres_etudiants pg
WHERE CONCAT('LMS-', LPAD(SUBSTRING(pg.matricule, 4), 5, '0'))
      IN (SELECT DISTINCT student_code FROM staging_mysql_notes)

UNION ALL

-- Orphelins MySQL (dans MySQL, pas dans PG)
SELECT NULL, m.student_code, NULL, NULL, NULL, NULL, NULL,
       FALSE, TRUE, NULL
FROM (
    SELECT DISTINCT student_code FROM staging_mysql_notes
) m
WHERE NOT EXISTS (
    SELECT 1 FROM staging_postgres_etudiants pg
    WHERE CONCAT('LMS-', LPAD(SUBSTRING(pg.matricule, 4), 5, '0')) = m.student_code
)

UNION ALL

-- Orphelins PostgreSQL (dans PG, pas dans MySQL)
SELECT pg.matricule,
       CONCAT('LMS-', LPAD(SUBSTRING(pg.matricule, 4), 5, '0')) AS student_code,
       pg.nom, pg.prenom, pg.email, pg.ville, pg.region,
       TRUE, FALSE, pg.date_creation
FROM staging_postgres_etudiants pg
WHERE CONCAT('LMS-', LPAD(SUBSTRING(pg.matricule, 4), 5, '0'))
      NOT IN (SELECT DISTINCT student_code FROM staging_mysql_notes);
```

## Impact sur les KPI du DG

Certains KPI demandés par le DG doivent tenir compte de ces catégories :

| KPI | Calcul recommandé |
|---|---|
| Nombre d'étudiants inscrits | 13 505 (uniques Aissata) |
| Nombre d'étudiants actifs | 15 000 (uniques MySQL) ou 12 606 (recoupés) selon définition |
| Taux d'engagement post-inscription | 12 606 / 13 505 = 93.4% |
| Étudiants sans activité (à relancer) | 899 |
| Étudiants LMS sans dossier admin (à investiguer) | 2 394 |

Ces définitions doivent être **validées avec le DG** avant de figurer dans les tableaux de bord finaux.
