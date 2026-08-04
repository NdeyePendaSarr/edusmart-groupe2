# EduSmart Academic — Génération d'un jeu de données académique "sale"

Projet de génération d'une base de données PostgreSQL fictive (gestion académique) contenant **volontairement** des anomalies de qualité de données, à des fins pédagogiques (nettoyage de données, data cleaning, ETL, contrôle qualité).

## 1. Objectif du projet

Simuler le système d'information d'un établissement de formation (`edusmart_academic`) avec des données réalistes en contexte sénégalais, mais délibérément imparfaites : valeurs manquantes, doublons, formats hétérogènes, catégories mal standardisées, incohérences métier et violations d'intégrité référentielle. Le jeu de données sert de support à des exercices de nettoyage/preprocessing avant chargement dans une base décisionnelle.

## 2. Contenu du dépôt

| Fichier | Rôle |
|---|---|
| `Source_1.pdf` | Cahier des charges : structure des 5 tables, contraintes métier, et liste des incohérences à injecter volontairement |
| `db_incorect.py` | Script principal : recrée le schéma PostgreSQL, génère et insère les données (avec `Faker`) |
| `gen_data.py` | Exporte le contenu des 5 tables PostgreSQL vers des fichiers CSV |

## 3. Modèle de données

5 tables, toutes en clé primaire `UUID` :

```
filieres (1) ──< classes (1) ──< inscriptions (N) >── etudiants (1)
                                        │
                                        └──< paiements (N)
```

- **etudiants** — identité, contact, localisation (région/ville au Sénégal)
- **filieres** — offre de formation (code, niveau, durée, coût)
- **classes** — rattachées à une filière, avec effectif et salle
- **inscriptions** — lien étudiant ↔ classe, avec statut, bourse, réduction
- **paiements** — historique des règlements, rattachés à une inscription

## 4. Volumétrie générée

| Table | Nombre de lignes |
|---|---|
| filieres | 13 |
| classes | 10 |
| etudiants | 15 000 |
| inscriptions | 14 905 |
| paiements | 14 907 |

## 5. Anomalies injectées volontairement

### `etudiants`
- **Doublons** : ~10 % des matricules valent `ETU1000` (matricule censé être unique)
- **Catégories non standardisées** : `sexe` prend 8 valeurs différentes (`M`, `F`, `Homme`, `Femme`, `Masculin`, `1`, `0`, valeur nulle) pour désigner en réalité 2 catégories
- **Incohérence métier** : ~10 % des dates de naissance sont dans le futur
- **Valeurs manquantes** : ~10 % des téléphones sont vides
- **Formats hétérogènes** : préfixes téléphoniques mélangés (`77…`, `+22177…`, `0022177…`)
- **Casse incohérente** : la région `kaffrine` apparaît en minuscule dans le référentiel des régions

### `filieres`
- **Redondance sémantique** : trois intitulés différents pour un même domaine (`IA`, `Intelligence Artificielle`, `Ingénierie IA`, `IA Advanced`)
- **Valeurs aberrantes** : une filière a une durée de 120 mois (10 ans)
- Certaines filières au statut `INACTIF`, à filtrer selon le cas d'usage

### `classes`
- **Violation d'intégrité référentielle** : ~20 % des classes référencent un `id_filiere` inexistant
- **Formats hétérogènes** : année académique en 3 formats (`2024-2025`, `2025-2026`, `2024/2025`) ; salle en 4 formats (`Salle A100`, `A100`, `A-100`, `B200`)
- **Valeurs aberrantes** : capacités incohérentes (de 10 à 500 places)

### `inscriptions`
- **Violation d'intégrité référentielle** : ~15 % des inscriptions référencent un `id_etudiant` inexistant
- **Incohérence métier** : ~10 % des dates d'inscription sont décalées de +500 jours (postérieures à la période attendue)
- **Statuts non standardisés** : `INSCRIT`, `EN ATTENTE`, `ANNULE`, mais aussi `UNKNOWN`
- **Catégories mal saisies** : `Nouvelle` / `NOUVELLE` / `Reinscription` / `Reinscription ` (espace parasite) / valeur nulle
- **Valeurs manquantes** : `bourse` peut être nulle
- **Violation de contrainte métier** : `reduction` peut être négative (`-20`) ou dépasser 100 (`150`), alors que la règle métier impose 0–100

### `paiements`
- **Violation d'intégrité référentielle** : ~20 % des paiements référencent une inscription inexistante
- **Doublons** : ~10 % des références valent `REF_DOUBLON_123` (la référence est censée être unique)
- **Valeurs aberrantes / violation de contrainte** : montants négatifs (`-15000`), nuls, ou irréalistes (`15 000 000`)
- **Catégories mal standardisées** : mode de paiement `OM` / `Orange Money` / `orange money` traités comme 3 valeurs distinctes
- **Valeurs manquantes** : `statut` peut être nul
- **Formats hétérogènes** : tranche exprimée en `1ere`, `2eme`, `Tranche 1`, `1`, etc.

## 6. Prérequis

- PostgreSQL (avec l'extension `uuid-ossp` disponible)
- Python 3, packages : `psycopg2`, `Faker`, `pandas`

```bash
pip install psycopg2-binary Faker pandas
```

## 7. Exécution

1. Adapter les paramètres de connexion (`host`, `database`, `user`, `password`) dans `db_incorect.py` et `gen_data.py`
2. Générer le schéma et les données :
   ```bash
   python db_incorect.py
   ```
3. Exporter les tables en CSV (dossier `regroupement/data/`) :
   ```bash
   python gen_data.py
   ```

## 8. Remarque

Les identifiants de connexion à la base sont actuellement écrits en clair dans les deux scripts. Pour un usage au-delà du cadre pédagogique local, il est recommandé de les externaliser (variables d'environnement, fichier `.env`).

## 9. Suite possible

Ce jeu de données est conçu comme point de départ à un pipeline de nettoyage : détection et traitement des doublons, standardisation des catégories, contrôle des contraintes métier (réductions, montants), résolution ou mise en quarantaine des lignes orphelines, avant chargement dans un modèle décisionnel.
