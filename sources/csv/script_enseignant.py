from faker import Faker
import pandas as pd
import random
from datetime import date, timedelta


# ============================================================
# 1) INITIALISATION
# ============================================================

fake = Faker("fr_FR")

NB_ENSEIGNANTS = 100  #



# ============================================================
# 2) LISTES METIER
# ============================================================

specialites = [
    "Intelligence Artificielle",
    "Data Science",
    "Génie Logiciel",
    "Cybersécurité",
    "Réseaux Informatiques",
    "Base de Données",
    "Développement Web",
    "Systèmes Informatiques",
    "Mathématiques",
    "Physique",
    "Chimie",
    "Biologie",
    "Médecine",
    "Pharmacie",
    "Droit",
    "Économie",
    "Gestion",
    "Finance",
    "Architecture",
    "Génie Civil",
    "Génie Électrique",
    "Communication"
]


statuts = [
    "Permanent",
    "Vacataire",
    "Contractuel"
]



# ============================================================
# 3) GRADE SELON L'ANCIENNETE
# ============================================================
#
# Règle métier : le grade dépend du nombre d'années depuis
# l'embauche. On ne tire PLUS au hasard dans toute la liste,
# sinon on peut avoir un "Professeur Titulaire" embauché
# il y a 6 mois, ce qui n'a aucun sens dans la vraie vie.

def choisir_grade(anciennete_annees):

    if anciennete_annees <= 2:
        # Début de carrière
        return random.choice(["Assistant", "Chargé de Cours"])

    elif anciennete_annees <= 5:
        return "Maître Assistant"

    elif anciennete_annees <= 9:
        return "Maître de Conférences"

    else:
        # 10 ans et plus -> haut grade
        return random.choice(["Professeur Titulaire", "Chercheur"])



# ============================================================
# 4) GENERATION DATE D'EMBAUCHE (fenêtre fixe : 2016 -> aujourd'hui)
# ============================================================
#
# On limite volontairement la fenêtre de recrutement à 10 ans.
# Pourquoi : si on laissait des dates d'embauche remonter à 1995
# ou 2000, il faudrait générer un salaire PAR MOIS depuis cette
# date jusqu'à aujourd'hui pour rester cohérent (historique de
# paie complet) -> des centaines de lignes de salaire par prof,
# donc un volume qui explose et devient ingérable pour un projet
# pédagogique. En bornant à 2016-2026, l'ancienneté max reste
# connue et petite (10 ans), donc le futur salaires.csv restera
# simple (on pourra se limiter aux 12 derniers mois par prof).
#
# NOTE TECHNIQUE : fake.date_between() a besoin de vrais objets
# date(), pas de texte "2016-01-01" (sinon ParseError avec la
# version de Faker installée ici).

def generate_hire_date():
    return fake.date_between(
        start_date=date(2016, 1, 1),
        end_date=date.today()
    )



# ============================================================
# 5) GENERATION DATE DE NAISSANCE (déduite de la date d'embauche)
# ============================================================
#
# On ne tire plus la date de naissance au hasard de manière
# indépendante. On part de la date d'embauche, on choisit un
# âge de recrutement réaliste (23 à 60 ans, comme dans le
# tableau de contraintes du sujet), puis on recule dans le
# temps pour obtenir la naissance. Ça garantit que naissance
# et embauche restent toujours cohérentes entre elles.
#
# On utilise 365.25 jours/an (et pas 365) pour éviter un petit
# décalage qui s'accumule sur des âges élevés (années bissextiles).

def generate_birth_date(date_embauche):

    age_recrutement = random.randint(23, 60)

    jours = int(age_recrutement * 365.25)

    date_naissance = date_embauche - timedelta(days=jours)

    return date_naissance, age_recrutement



# ============================================================
# 6) GENERATION D'UN ENSEIGNANT
# ============================================================

def generate_teacher(numero):

    profil = fake.simple_profile()
    prenom = profil["name"].split()[0]

    # Sexe Faker : M = Homme, F = Femme
    sexe = "H" if profil["sex"] == "M" else "F"

    date_embauche = generate_hire_date()

    date_naissance, age_recrutement = generate_birth_date(date_embauche)

    # Ancienneté = nombre d'années entières depuis l'embauche
    anciennete_annees = date.today().year - date_embauche.year

    grade = choisir_grade(anciennete_annees)

    enseignant = {
        "teacher_code": f"TEACH-{numero:03d}",
        "nom": fake.last_name(),
        "prenom": prenom,
        "sexe": sexe,
        "date_naissance": date_naissance,
        "telephone": fake.phone_number(),
        "email": fake.email(),
        "specialite": random.choice(specialites),
        "grade": grade,
        "date_embauche": date_embauche,
        "statut": random.choice(statuts)
    }

    return enseignant



# ============================================================
# 7) GENERATION DE TOUS LES ENSEIGNANTS (données propres)
# ============================================================

liste_enseignants = []

for i in range(1, NB_ENSEIGNANTS + 1):
    liste_enseignants.append(generate_teacher(i))

df = pd.DataFrame(liste_enseignants)



# ============================================================
# 8) ANOMALIES - VALEURS MANQUANTES (1%)
# ============================================================
#
# Le sujet autorise explicitement telephone et email à être
# vides. On simule aussi un oubli RH sur specialite et grade.

nombre_cellules = df.size
nombre_manquants = int(nombre_cellules * 0.01)

colonnes_autorisees = ["telephone", "email", "specialite", "grade"]

for _ in range(nombre_manquants):
    ligne = random.randint(0, len(df) - 1)
    colonne = random.choice(colonnes_autorisees)
    df.loc[ligne, colonne] = None



# ============================================================
# 9) ANOMALIES - SPECIALITES MAL ORTHOGRAPHIEES / ABREGEES
# ============================================================
#
# Demandé explicitement dans le sujet : "IA", "Intelligence
# Artificielle", "Data Science" écrits différemment pour
# désigner la même chose. On remplace au hasard quelques
# valeurs propres par une variante mal écrite.

variantes_specialite = {
    "Intelligence Artificielle": ["IA", "intelligence artificielle", "I.A"],
    "Data Science": ["data science", "DataScience", "Data-Science"],
    "Base de Données": ["BDD", "Base de donnees", "base de données"],
    "Génie Logiciel": ["genie logiciel", "Génie Log."],
}

nombre_variantes = int(len(df) * 0.03)  # ~3% des lignes touchées

for _ in range(nombre_variantes):
    ligne = random.randint(0, len(df) - 1)
    valeur_actuelle = df.loc[ligne, "specialite"]

    if valeur_actuelle in variantes_specialite:
        df.loc[ligne, "specialite"] = random.choice(variantes_specialite[valeur_actuelle])



# ============================================================
# 10) ANOMALIES - TELEPHONES MAL FORMATES
# ============================================================
#
# On casse volontairement le format Faker sur quelques lignes :
# espaces mal placés, indicatif pays supprimé, points au lieu
# d'espaces, ou tout collé sans séparateur. Ça simule une
# saisie RH non standardisée (demandé dans les recommandations).

def casser_format_telephone(numero_str):
    style = random.choice(["espaces", "sans_indicatif", "points", "brut"])

    chiffres = "".join(c for c in numero_str if c.isdigit())

    if style == "espaces":
        return " ".join([chiffres[i:i+2] for i in range(0, len(chiffres), 2)])
    elif style == "sans_indicatif":
        return chiffres[-9:]  # coupe l'indicatif pays
    elif style == "points":
        return ".".join([chiffres[i:i+2] for i in range(0, len(chiffres), 2)])
    else:
        return chiffres  # tout collé, sans séparateur


nombre_tel_casses = int(len(df) * 0.05)  # ~5% des numéros

for _ in range(nombre_tel_casses):
    ligne = random.randint(0, len(df) - 1)
    valeur_actuelle = df.loc[ligne, "telephone"]

    if pd.notna(valeur_actuelle):
        df.loc[ligne, "telephone"] = casser_format_telephone(valeur_actuelle)



# ============================================================
# 11) ANOMALIES - GRADES INCOHERENTS
# ============================================================
#
# Le sujet demande volontairement des grades incohérents.
# On force quelques lignes à "Professeur Titulaire" sans tenir
# compte de l'ancienneté réelle (erreur de saisie RH plausible).

nombre_grades_incoherents = int(len(df) * 0.02)  # ~2%

for _ in range(nombre_grades_incoherents):
    ligne = random.randint(0, len(df) - 1)
    df.loc[ligne, "grade"] = "Professeur Titulaire"



# ============================================================
# 12) ANOMALIES - DOUBLONS (1%)
# ============================================================

nombre_doublons = int(NB_ENSEIGNANTS * 0.01)

lignes_dupliquees = df.sample(max(nombre_doublons, 1))

df = pd.concat([df, lignes_dupliquees], ignore_index=True)



# ============================================================
# 13) VERIFICATION
# ============================================================

print("\n========== APERCU ==========")
print(df.head())

print("\nNombre total lignes :", len(df))

print("\nValeurs manquantes :")
print(df.isnull().sum())

print("\nExemples de spécialités (variantes incluses) :")
print(df["specialite"].value_counts().head(10))



# ============================================================
# 14) EXPORT CSV
# ============================================================

df.to_csv(
    "enseignants.csv",
    sep=";",
    encoding="utf-8",
    index=False
)

print("\nFichier enseignants.csv généré avec succès")