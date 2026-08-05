# EduSmart MySQL v2 — Package de l'équipe MySQL

Package MySQL professionnel pour la source **edusmart_learning_v2** du projet **EduSmart Decision Platform** (module BI).

Ce package permet à chaque membre de l'équipe MySQL de reconstruire une base MySQL locale **identique** à celle des autres membres, à partir des CSV partagés sur le Drive.

---

## 🎯 Objectif

Chaque membre du projet EduSmart doit avoir les 5 bases de données sur sa machine (PostgreSQL, MySQL, MongoDB, Redis, CSV RH). Ce package concerne la source MySQL uniquement.

L'objectif est que **les 5 membres de l'équipe MySQL** (un par groupe de la classe) aient tous **exactement les mêmes données** dans leur base MySQL locale.

---

## 📂 Structure du package

```
edusmart-mysql-v2/
├── create_database.sql       # Script SQL : crée la base et les 6 tables
├── insert_data.py            # Charge les CSV du Drive dans MySQL
├── extract_mysql.py          # Extrait les 6 tables vers data/staging/ (pour l'ETL)
├── test_data_quality.py      # Tests automatiques de qualité (26 tests)
├── data/
│   ├── input/                # Y placer les 6 CSV du Drive
│   └── staging/              # Sorties d'extraction
├── docs/
│   ├── anomalies.md          # Documentation des 18 anomalies volontaires
│   └── inter-source-mapping.md  # Cohérence avec PostgreSQL (Aissata)
├── logs/                     # Logs d'exécution
├── .env.example              # Modèle pour les identifiants MySQL
├── .gitignore
├── requirements.txt          # Dépendances Python
└── README.md                 # Ce fichier
```

---

## ⚙️ Prérequis

- **Python** 3.9 ou supérieur
- **MySQL Server** 8.0 ou supérieur (avec un compte utilisateur ayant les privilèges CREATE, INSERT, SELECT)
- **Les 6 fichiers CSV** partagés sur le Drive :
  - `modules.csv` (500 lignes, 55 Ko)
  - `cours.csv` (2 000 lignes, 257 Ko)
  - `quiz.csv` (5 000 lignes, 530 Ko)
  - `notes.csv` (500 000 lignes, 55 Mo)
  - `progression.csv` (15 000 lignes, 2 Mo)
  - `temps_connexion.csv` (80 000 lignes, 9.4 Mo)

---

## 🚀 Installation étape par étape

### Étape 1 — Récupérer le package

Cloner le dépôt ou décompresser l'archive :

```bash
cd C:\Projets\
# soit :
git clone <url-du-depot> edusmart-mysql-v2
# soit :
# décompresser edusmart-mysql-v2.zip
cd edusmart-mysql-v2
```

### Étape 2 — Créer un environnement virtuel Python

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### Étape 3 — Configurer les identifiants MySQL

Copier `.env.example` en `.env` et adapter les valeurs :

```bash
# Windows
copy .env.example .env
# Linux / Mac
cp .env.example .env
```

Éditer `.env` :

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=votre_user
MYSQL_PASSWORD=votre_password
MYSQL_DATABASE=edusmart_learning_v2
```

### Étape 4 — Placer les CSV du Drive

Télécharger les 6 CSV depuis le Drive commun de l'équipe MySQL et les placer dans `data/input/` :

```
data/input/
├── modules.csv
├── cours.csv
├── quiz.csv
├── notes.csv
├── progression.csv
└── temps_connexion.csv
```

### Étape 5 — Créer la base et les tables

```bash
mysql -u root -p < create_database.sql
```

Attendu : les 6 tables sont créées, `SHOW TABLES;` liste `cours`, `modules`, `notes`, `progression`, `quiz`, `temps_connexion`.

### Étape 6 — Charger les données

```bash
python insert_data.py
```

Durée typique : **2 à 5 minutes** selon la machine (500 000 notes à insérer).

Vérifier le fichier `logs/insert_data.log` pour le détail.

**Bilan attendu :**
```
[OK] modules            :      500 inserees,      0 echouees en   0.15s
[OK] cours              :     2000 inserees,      0 echouees en   0.60s
[OK] quiz               :     5000 inserees,      0 echouees en   1.50s
[OK] notes              :   500000 inserees,      0 echouees en 150.00s
[OK] progression        :    15000 inserees,      0 echouees en   4.00s
[OK] temps_connexion    :    80000 inserees,      0 echouees en  24.00s
```

### Étape 7 — Vérifier avec les tests

```bash
python test_data_quality.py
```

Attendu : **26 tests, tous OK**. Si un test échoue, consulter `logs/test_data_quality.log`.

### Étape 8 — Extraire pour l'ETL (Phase B)

Une fois la base peuplée, l'extraction pour le pipeline BI :

```bash
python extract_mysql.py
```

Sortie : 6 fichiers `mysql_*.csv` dans `data/staging/` + un fichier `metadata_extract_mysql.json`.

---

## 🧪 Vérifications rapides en SQL

Se connecter à MySQL et exécuter :

```sql
USE edusmart_learning_v2;

-- Volumes attendus
SELECT 'modules'         AS table_name, COUNT(*) AS n FROM modules
UNION ALL SELECT 'cours',          COUNT(*) FROM cours
UNION ALL SELECT 'quiz',           COUNT(*) FROM quiz
UNION ALL SELECT 'notes',          COUNT(*) FROM notes
UNION ALL SELECT 'progression',    COUNT(*) FROM progression
UNION ALL SELECT 'temps_connexion', COUNT(*) FROM temps_connexion;

-- Résultat attendu :
--   modules         :    500
--   cours           :   2000
--   quiz            :   5000
--   notes           : 500000
--   progression     :  15000
--   temps_connexion :  80000
```

---

## 🎓 Choix techniques et cohérence

### Format des identifiants

- **id_module, id_cours, id_quiz, id_note, id_progression, id_connexion** : UUID stockés en `CHAR(36)`
- **code_module** : format `MOD-XXX` (unique)
- **student_code** : format `LMS-XXXXX` (5 chiffres, ex: `LMS-00001` à `LMS-15000`)

### Cohérence avec PostgreSQL (Aissata)

Le `student_code` MySQL est **partiellement dérivé** des matricules PostgreSQL d'Aissata via la règle :

```python
student_code = "LMS-" + matricule[3:].zfill(5)
```

Sur les 15 000 étudiants MySQL :
- **12 606 matchent** les matricules d'Aissata
- **2 394 sont orphelins** (dans MySQL, pas chez Aissata) : LMS-00001 à LMS-00999 + quelques autres
- **899 étudiants Aissata** n'ont pas d'activité MySQL

Voir [`docs/inter-source-mapping.md`](docs/inter-source-mapping.md) pour le détail et l'impact sur les KPI.

### Anomalies volontaires

18 anomalies sont volontairement présentes dans les données. Elles simulent les problèmes réels que le pipeline ETL de la Phase B devra traiter.

Voir [`docs/anomalies.md`](docs/anomalies.md) pour le détail complet avec taux observés et recommandations de nettoyage.

---

## 📊 Volumes finaux

| Table | Volume | Taille CSV |
|---|---|---|
| modules | 500 | 55 Ko |
| cours | 2 000 | 257 Ko |
| quiz | 5 000 | 530 Ko |
| notes | 500 000 | 55 Mo |
| progression | 15 000 | 2 Mo |
| temps_connexion | 80 000 | 9.4 Mo |
| **TOTAL** | **602 500 lignes** | **~68 Mo** |

---

## 🔧 Résolution de problèmes

### « Access denied for user »

Vérifier que le fichier `.env` contient les bons identifiants et que l'utilisateur a les privilèges nécessaires :

```sql
CREATE USER 'edusmart_user'@'localhost' IDENTIFIED BY 'change_me';
GRANT ALL PRIVILEGES ON edusmart_learning_v2.* TO 'edusmart_user'@'localhost';
FLUSH PRIVILEGES;
```

### « Fichier .csv introuvable »

S'assurer que les 6 CSV sont bien placés dans `data/input/` (pas dans le dossier racine du projet).

### « Erreur d'encodage »

Les CSV utilisent le séparateur `;` (point-virgule) et l'encodage UTF-8 (avec ou sans BOM). Le script gère les deux cas automatiquement.

### Test échoué : « Volume progression »

Si le chargement s'est arrêté avant la fin (déconnexion, timeout), relancer :

```bash
mysql -u root -p < create_database.sql   # remet la base à zéro
python insert_data.py                    # recharge tout
```

### L'insertion des notes est très lente

C'est normal, 500 000 lignes prennent 2 à 5 minutes. Le script affiche la progression toutes les 100 000 lignes. Ne pas interrompre.

---

## 📞 Contact et coordination

**Équipe MySQL** — Groupes 1 à 5 de la classe

**Références du projet :**
- Spécification Source 2 (MySQL) : voir le PDF sur le Drive commun
- Pipeline BI global : ETL vers Data Warehouse, prévu en Phase B
- Autres sources : PostgreSQL (Aissata), MongoDB (Mouhameth), Redis (Seydina), CSV RH (Bachir)

---

## 📄 Licence

Projet pédagogique universitaire — Usage interne uniquement.
