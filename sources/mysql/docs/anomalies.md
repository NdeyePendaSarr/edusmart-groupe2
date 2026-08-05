# Documentation des anomalies volontaires — MySQL v2

Ce document liste les anomalies volontairement présentes dans les CSV du Drive, avec leurs taux réels observés, leurs impacts sur l'intégrité, et les recommandations de traitement pour le pipeline ETL de la Phase B.

Ces anomalies simulent les problèmes qu'on rencontre en environnement réel de production. Elles ne sont pas des défauts : elles sont là pour permettre à `transform.py` de s'exercer sur du nettoyage.

---

## Vue d'ensemble

| # | Code | Type d'anomalie | Table | Taux observé | Impact |
|---|---|---|---|---|---|
| 1 | A1 | Variantes de catégories | modules | 10 catégories | Standardisation nécessaire |
| 2 | A2 | Modules inactifs | modules | 27.6% | Filtre à appliquer |
| 3 | A3 | Statuts variés dans cours | cours | ~30% BROUILLON/ARCHIVE | Filtre à appliquer |
| 4 | A4 | Types de cours divers | cours | plusieurs valeurs | Standardisation possible |
| 5 | A5 | Durées de quiz aberrantes | quiz | rare | À vérifier |
| 6 | A6 | Scores négatifs | notes | 7.7% (38 554) | Nettoyage |
| 7 | A7 | Tentatives négatives | notes | 33% (165 590) | Nettoyage |
| 8 | A8 | Progressions > 100% | progression | 29% (4 345) | Cap à 100% ou rejet |
| 9 | A9 | Progressions < 0% | progression | 11.7% (1 753) | Floor à 0% ou rejet |
| 10 | A10 | dernier_cours fantôme | progression | 69% (10 410) | Set NULL |
| 11 | A11 | id_module fantôme | progression | 10.2% (1 525) | Rejet ou création |
| 12 | A12 | Variantes d'appareils | temps_connexion | 9 valeurs | Standardisation |
| 13 | A13 | Durées connexion < 0 | temps_connexion | 19.7% (15 768) | Absolute ou rejet |
| 14 | A14 | IP vides / NULL | temps_connexion | 9.85% (7 881) | Conserver NULL |
| 15 | A15 | IP invalides | temps_connexion | à mesurer | Set NULL |
| 16 | A16 | Dates incohérentes | temps_connexion | rare | À vérifier |
| 17 | A17 | student_codes orphelins | notes, progression, temps_connexion | ~16% | Mapping ETL |
| 18 | A18 | Colonnes NULL | temps_connexion | variable | Conserver ou déduire |

---

## Détail des anomalies

### A1 — Variantes de catégories dans `modules`

**Description :** Les catégories de modules sont écrites de plusieurs façons différentes, simulant des saisies non standardisées.

**Valeurs observées** : `Data`, `DATA`, `data science`, `Cloud`, `Base de données`, `Sécurité`, `Développement`, `Réseau`, `IA`, `DevOps`.

**Volume :** 10 catégories distinctes (attendu : 5-6 après nettoyage)

**Traitement ETL recommandé :**
```sql
-- Standardiser en UPPERCASE + trim
UPDATE dim_module SET categorie = UPPER(TRIM(categorie));

-- Mapper les variantes vers une liste canonique
-- ('DATA', 'DATA SCIENCE') -> 'DATA_SCIENCE'
-- ('SECURITE', 'SECURITY') -> 'CYBERSECURITE'
```

**Seuil de tolérance :** Aucun rejet, 100% mappable.

---

### A2 — Modules inactifs

**Description :** 27.6% des modules ont `actif = FALSE`. Ces modules ne devraient pas être proposés aux étudiants, mais ils apparaissent dans les données historiques.

**Volume :** 138 modules sur 500 (27.6%)

**Traitement ETL recommandé :**
- **Pour le DW** : garder tous les modules dans `dim_module` avec un flag `is_active`
- **Pour les KPI d'engagement** : filtrer sur `is_active = TRUE`
- **Pour l'analyse d'abandon** : conserver les modules inactifs (peuvent expliquer les baisses de progression)

**Seuil de tolérance :** taux entre 15% et 40% attendu.

---

### A3 — Statuts variés dans `cours`

**Description :** Les cours ont plusieurs statuts (`PUBLIE`, `BROUILLON`, `ARCHIVE`), alors que la spec initiale mentionnait uniquement `PUBLIE`.

**Traitement ETL recommandé :**
- Ne charger dans le DW que les cours `statut = 'PUBLIE'`
- Ou conserver tous les statuts avec un attribut de filtrage

---

### A5 — Durées de quiz aberrantes

**Description :** Certains quiz ont des `duree_minutes` négatives ou très élevées (> 300 min).

**Traitement ETL recommandé :**
```sql
CASE
    WHEN duree_minutes <= 0 OR duree_minutes > 300 THEN NULL
    ELSE duree_minutes
END AS duree_minutes_cleaned
```

---

### A6 — Scores négatifs et tentatives négatives dans `notes`

**Description :** Deux anomalies distinctes sur la table notes :
- **A6a** : 38 554 notes (7.7%) ont un `score < 0`
- **A6b** : 165 590 notes (33%) ont une `tentative < 0`

**Traitement ETL recommandé :**
```sql
-- Score : les négatifs sont probablement des erreurs de saisie
CASE WHEN score < 0 THEN NULL ELSE score END

-- Tentative : les négatifs sont invalides, remettre à 1
CASE WHEN tentative < 1 THEN 1 ELSE tentative END
```

**Alternative :** rejeter ces lignes dans une table de quarantaine pour analyse.

**Seuil de tolérance ETL :**
- Score négatif : entre 3% et 15%
- Tentative négative : entre 20% et 45%

---

### A8 — Progressions supérieures à 100%

**Description :** 4 345 progressions sur 15 000 (29%) ont un pourcentage > 100.

**Traitement ETL recommandé :**
```sql
-- Option 1 : cap à 100%
LEAST(pourcentage, 100) AS pourcentage_cleaned

-- Option 2 : rejet en quarantaine
WHERE pourcentage <= 100
```

**Recommandation :** Option 1 pour ne pas perdre les étudiants concernés dans les analyses.

---

### A9 — Progressions négatives

**Description :** 1 753 progressions (11.7%) ont un pourcentage < 0.

**Traitement ETL recommandé :**
```sql
GREATEST(pourcentage, 0) AS pourcentage_cleaned
```

---

### A10 — `dernier_cours` fantôme dans progression

**Description :** 10 410 progressions (69%) référencent un `dernier_cours` qui n'existe pas dans la table `cours`.

**Important :** C'est une anomalie **très forte** en volume, à traiter avec soin.

**Traitement ETL recommandé :**
```sql
CASE
    WHEN dernier_cours NOT IN (SELECT id_cours FROM cours) THEN NULL
    ELSE dernier_cours
END AS dernier_cours_cleaned
```

**Rappel :** Aucune FK n'est posée dans le schéma pour cette raison.

---

### A11 — `id_module` fantôme dans progression

**Description :** 1 525 progressions (10.2%) référencent un `id_module` qui n'existe pas.

**Traitement ETL recommandé :**
- Option 1 : rejet en quarantaine
- Option 2 : ne pas rattacher au dimensional model (progression "orpheline")

**Rappel :** Aucune FK n'est posée dans le schéma pour cette raison.

---

### A12 — Variantes d'appareils

**Description :** 9 valeurs distinctes d'appareils, dont plusieurs doublons sémantiques.

**Valeurs observées :**
- `Mobile`, `mobile`, `Téléphone`, `iPhone`, `Android` → tous = mobile
- `Tablette`, `iPad` → tous = tablette
- `PC`, `Ordinateur` → tous = desktop

**Traitement ETL recommandé :**
```sql
CASE
    WHEN LOWER(appareil) IN ('mobile', 'téléphone', 'telephone', 'iphone', 'android') THEN 'MOBILE'
    WHEN LOWER(appareil) IN ('tablette', 'ipad') THEN 'TABLETTE'
    WHEN LOWER(appareil) IN ('pc', 'ordinateur') THEN 'DESKTOP'
    ELSE 'INCONNU'
END AS appareil_normalise
```

---

### A13 — Durées de connexion négatives

**Description :** 15 768 connexions (19.7%) ont `duree_minutes < 0`.

**Traitement ETL recommandé :**
```sql
CASE
    WHEN duree_minutes < 0 THEN NULL  -- ou ABS(duree_minutes)
    ELSE duree_minutes
END
```

**Alternative :** recalculer depuis `date_deconnexion - date_connexion` si les deux sont valides.

---

### A14 — IP vides ou NULL

**Description :** 7 881 connexions (9.85%) n'ont pas d'IP renseignée.

**Traitement ETL recommandé :** Conserver NULL. Utile pour détecter les connexions "anonymes" ou les problèmes de tracking.

---

### A17 — student_codes orphelins par rapport à Aissata

**Description :** Sur 15 000 student_codes utilisés dans MySQL :
- **12 606 matchent** les matricules d'Aissata (dérivation : `LMS-` + `matricule[3:].zfill(5)`)
- **2 394 sont orphelins** (LMS-00001 à LMS-00999 principalement)
- **899 étudiants Aissata** n'ont aucune trace dans MySQL

**Traitement ETL recommandé :**
- Créer une dimension `dim_etudiant` en union outer join
- Ajouter un flag `has_admin_record` (True si présent chez Aissata)
- Ajouter un flag `has_lms_activity` (True si présent dans MySQL)

**Impact pour les KPI :**
- Nombre d'étudiants **inscrits** (source : PostgreSQL) : 13 505 uniques
- Nombre d'étudiants **actifs sur LMS** (source : MySQL) : 15 000
- Nombre d'étudiants **connus des deux systèmes** : 12 606
- Écart à documenter dans le rapport BI final

---

## Résumé pour le pipeline ETL

Le tableau ci-dessous synthétise les décisions de traitement recommandées :

| Anomalie | Action ETL | Perte de données ? |
|---|---|---|
| A1 | Standardiser | Non |
| A2 | Filtrer si nécessaire | Non |
| A3 | Filtrer `PUBLIE` seulement | Oui (partielle) |
| A5 | Nullifier | Non |
| A6a | Nullifier | Non |
| A6b | Forcer à 1 | Non |
| A8 | Cap à 100 | Non |
| A9 | Floor à 0 | Non |
| A10 | Nullifier `dernier_cours` | Non |
| A11 | Rejeter en quarantaine | Oui (1.5k lignes) |
| A12 | Standardiser | Non |
| A13 | Nullifier ou recalculer | Non |
| A14 | Conserver NULL | Non |
| A17 | Marquer avec flags | Non |

**Volume estimé après nettoyage :**
- Modules : 500 (100%)
- Cours : ~1 400 (70% après filtre PUBLIE)
- Quiz : 5 000 (100%)
- Notes : 500 000 (100%, nettoyage inline)
- Progression : 13 475 (89.8%, après rejet des 1 525 fantômes)
- Connexions : 80 000 (100%, nettoyage inline)

**Total dans le DW : ~1 million de lignes exploitables.**
