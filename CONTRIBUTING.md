# Guide de contribution - EduSmart Decision Platform

## Organisation Git

Le projet utilise trois niveaux de branches :

```
main
 |
dev
 |
feature/*
```

## Branches

### main

Branche stable contenant les versions validées du projet.

### dev

Branche principale de développement. Toutes les fonctionnalités doivent être intégrées ici avant la mise en production.

### Branches personnelles

Chaque membre doit créer une branche dédiée :

* feature/postgresql-aissata
* feature/mysql-penda
* feature/csv-bachir
* feature/mongodb-mouhameth
* feature/redis-seydine

---

# Workflow de développement

Avant de commencer un travail :

```bash
git checkout dev
git pull origin dev
```

Créer une branche :

```bash
git checkout -b feature/nom-fonctionnalite
```

Après développement :

```bash
git add .
git commit -m "Description claire de la modification"
git push origin nom-de-la-branche
```

---

# Règles de commit

Les messages doivent être explicites.

Exemples :

```
Ajout génération données MySQL
Correction extraction MongoDB
Création table dimension étudiant
Nettoyage données CSV RH
```

Éviter :

```
update
test
modif
correction
```

---

# Organisation du projet

```
sources/
├── postgresql/
├── mysql/
├── csv/
├── mongodb/
└── redis/

etl/
├── extraction/
├── transformation/
└── loading/

warehouse/

docs/
```

---

# Règles de développement

Chaque membre doit :

* documenter sa source ;
* fournir un script de génération des données ;
* introduire volontairement des anomalies ;
* fournir un extracteur ;
* tester son code avant intégration.

---

# Processus d'intégration

1. Développement sur une branche personnelle.
2. Vérification du code.
3. Fusion vers dev.
4. Validation finale.
5. Fusion vers main.
