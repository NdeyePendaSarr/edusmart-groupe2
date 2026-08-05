# README de présentation — Redis Source / EduSmart

Ce projet simule un flux de données temps réel pour la plateforme EduSmart, en utilisant Redis comme moteur de stockage temporaire. L’objectif est de produire des événements réalistes d’activité utilisateur, puis de les insérer dans des structures Redis adaptées à l’analyse en temps réel.

## 1. Structure de la source

```text
redis_source/
├── anomalies.py
├── config.py
├── events.py
├── generate_data.py
├── insert_data.py
├── main.py
├── utils.py
├── data.json
├── file/
│   ├── cours.csv
│   └── quiz.csv
└── README.md
```

### Rôle des principaux fichiers

- config.py : centralise la configuration de connexion Redis.
- events.py : génère les événements “normaux” de l’activité des étudiants.
- anomalies.py : injecte des anomalies volontairement afin de reproduire des données bruitées.
- generate_data.py : choisit aléatoirement entre un événement normal et une anomalie.
- insert_data.py : transforme chaque événement en opérations Redis concrètes.
- main.py : point d’entrée du simulateur.
- utils.py : utilitaires de lecture des fichiers CSV et JSON.

## 2. Relations internes

Le fonctionnement du projet repose sur un flux simple et clair :

1. events.py génère des événements métier tels que LOGIN, LOGOUT, COURSE_OPEN, PROGRESS_UPDATE, QUIZ_COMPLETED ou NOTIFICATION.
2. anomalies.py peut modifier certains événements pour produire des cas anormaux.
3. generate_data.py décide si l’événement envoyé au système est normal ou anomalique.
4. insert_data.py reçoit cet événement et le mappe vers des commandes Redis comme HSET, SET, LPUSH, ZADD, EXPIRE, INCR, DECR ou DEL.
5. main.py orchestre la boucle de simulation et peut conserver les événements dans un fichier JSON.

En pratique, les modules sont découplés par responsabilité :

- la génération des événements est indépendante de la persistance Redis ;
- l’insertion Redis ne dépend pas de la logique métier de génération ;
- les anomalies sont ajoutées au niveau du générateur, sans casser le flux principal.

## 3. Contraintes mises en place

Le simulateur applique plusieurs contraintes pour rester réaliste :

- les étudiants ne peuvent se connecter qu’une seule fois à la fois ; les connexions doublons ne sont pas autorisées tant qu’une session est active ;
- les actions sensibles comme COURSE_OPEN, PROGRESS_UPDATE ou NOTIFICATION ne peuvent être produites que pour des étudiants déjà connectés ;
- les sessions sont associées à des identifiants uniques et à des métadonnées de connexion (appareil, IP, horodatage) ;
- les statistiques sont agrégées dans une structure Redis dédiée, avec une clé de type HASH ;
- la connexion Redis est configurée sur localhost:6379, base 0 ;
- la génération est déterministe grâce à une seed fixe (random.seed(42)), ce qui facilite la reproductibilité.

## 4. Anomalies introduites volontairement

Pour rendre les données plus proches des cas réels, plusieurs anomalies sont injectées de manière contrôlée :

- session expirée : une session reste présente alors qu’elle devrait avoir été supprimée ;
- étudiant inconnu : un événement est produit avec un identifiant d’étudiant hors référentiel courant ;
- notification en double : la même notification est ajoutée plusieurs fois à la liste ;
- progression invalide : une progression dépasse 100 % ;
- événement de session avec état incohérent : la session est marquée comme active alors que son horodatage suggère qu’elle devrait être expirée.

Ces anomalies sont volontairement ajoutées pour permettre de tester des traitements de nettoyage, de validation et d’analyse de qualité de données.

## 5. Volume de données généré

Le jeu de données actuellement disponible dans data.json contient 15 817 événements enregistrés.

Ce volume correspond à une simulation générée à partir de :

- 49 999 identifiants étudiants simulés (de LMS-000001 à LMS-049999) ;
- un jeu de cours et de quiz chargé depuis les fichiers CSV de la structure file/ ;
- un flux d’événements réparti entre événements normaux et anomalies.

## 6. Résumé du modèle

Le projet est un mini-simulateur de données temps réel conçu pour illustrer :

- la génération d’événements utilisateur ;
- l’introduction d’anomalies contrôlées ;
- la transformation de ces événements en structures Redis ;
- l’usage de Redis pour des cas d’usage orientés observabilité et qualité des données.


## 7. Difficultés
### 7.1 Architecture du projet
#### Problème

Déterminer une architecture claire tout en séparant la génération des données de leur insertion dans Redis.

#### Solution

Séparer le projet en plusieurs modules ayant chacun une responsabilité unique :
### 7.2 Génération des anomalies
#### Problème

Créer des anomalies réalistes sans dupliquer toute la logique des événements normaux.

#### Solution

Construire les anomalies à partir des événements existants en modifiant uniquement les informations nécessaires.


## 8. Compétences mises en œuvre

* Modélisation NoSQL
* Redis
* Python
* Simulation de données
* Génération d'anomalies
* Architecture logicielle
* Manipulation des structures Redis
* Gestion des données temps réel


## 9. Charger les données dans Redis avec Docker

### 9.1. Prérequis

- Python 3
- Docker
- Le projet téléchargé

### 9.2. Démarrer Redis

Téléchargez l'image Redis (si nécessaire) puis lancez un conteneur :

```bash
docker run -d --name redis-server -p 6379:6379 redis:latest
```

Si le conteneur existe déjà :

```bash
docker start redis-server
```

Vérifiez que Redis fonctionne :

```bash
docker exec -it redis-server redis-cli ping
```

Réponse attendue :

```text
PONG
```

### 9.3. Se placer dans le projet

```bash
cd /chemin/vers/redis_source
```

### 9.4. Créer un environnement virtuel

```bash
python3 -m venv env
source env/bin/activate
```

### 9.5. Installer les dépendances

```bash
pip install redis
```

### 9.6. Exécuter le programme

```bash
python main.py
```

Le programme lit le fichier `data.json` et insère les événements dans Redis.

### 9.7. Vérifier les données

Ouvrir Redis :

```bash
docker exec -it redis-server redis-cli
```

Lister les clés :

```redis
KEYS *
```

Afficher une session :

```redis
HGETALL session:<session_id>
```

Afficher les utilisateurs connectés :

```redis
SMEMBERS online_users
```

### 9.8. Arrêter Redis

```bash
docker stop redis-server
```

### 9.9. À retenir

Si vous débutez, l’idée importante est la suivante :

- data.json = le fichier contenant les événements à charger ;
- Redis = la base qui stocke ces événements sous forme de clés/valeurs ;
- insert_data.py = le pont entre les deux.

En résumé, le processus est :

```text
data.json -> lecture Python -> traitement des événements -> insertion dans Redis
```

## Conclusion

Ce projet a permis de comprendre le rôle de Redis dans une architecture de données temps réel ainsi que les différences fondamentales entre une base relationnelle et une base clé-valeur.

La simulation met en évidence les principaux usages de Redis dans une plateforme e-learning : gestion des sessions, suivi en temps réel, notifications, classements et statistiques.

L'ajout d'anomalies rend les données plus proches d'un environnement réel et facilite la validation de futurs traitements de contrôle qualité et d'analyse des données.

## Auteur

**Yero BA**

