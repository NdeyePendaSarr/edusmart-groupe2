import csv
import random
from faker import Faker

# Initialisation standard de Faker
fake = Faker('fr_FR')


enseignants = []  

annee_courante = 2026  # dernière année à générer pour tous les enseignants

with open("enseignants.csv", mode="r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter=';')
    fieldnames = reader.fieldnames or []

    # Adapter le nom de colonne ci-dessous si besoin (ex: "code", "matricule", "id_enseignant")
    colonne_code = "teacher_code"

    # Adapter le nom de colonne ci-dessous si besoin (ex: "date_embauche", "date_recrutement")
    colonne_embauche = "date_embauche"

    for row in reader:
        valeur_embauche = row[colonne_embauche]
        # Extraction de l'année, que la colonne contienne une date complète (ex: 2021-09-01) ou juste l'année
        date_embauche = int(str(valeur_embauche)[:4])
        enseignants.append({"code": row[colonne_code], "date_embauche": date_embauche})

mois_liste = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
              "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

# Liste des différents modes de paiement demandés (avec variantes d'écriture)
modes_paiement = ["Virement", "Banque", "bank transfer", "Wave", "Chèque", None]

data = []
id_salaire = 1

# 1. Génération normale respectant les contraintes métiers
# Contrainte métier : les salaires d'un enseignant démarrent à son année d'embauche
for enseignant in enseignants:
    Teacher_code = enseignant["code"]
    for annee in range(enseignant["date_embauche"], annee_courante + 1):
        for mois in mois_liste:
            # Valeurs standards cohérentes
            base = round(random.uniform(150000, 450000), 2)
            primes = round(random.uniform(10000, 150000), 2)
            retenues = round(random.uniform(5000, 100000), 2)
            # Contrainte métier : le salaire net est calculé
            net = round(base + primes - retenues, 2)
            mode = random.choice(modes_paiement)
            data.append([id_salaire, Teacher_code, mois, annee, base, primes, retenues, net, mode if mode else ""])
            id_salaire += 1

# Recommandation : Doublons (copie exacte d'une ligne existante avec un nouvel ID)
if data:
    doublon_ligne = data[0].copy()
    doublon_ligne[0] = id_salaire  # Même données mais nouvel ID pour tester les doublons métiers
    data.append(doublon_ligne)
    id_salaire += 1

# Écriture dans le fichier CSV
with open("salaires.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # En-tête du fichier
    writer.writerow([
        "id_salaire", "teacher_code", "mois", "annee",
        "salaire_base", "primes", "retenues", "salaire_net", "mode_paiement"
    ])
    # Lignes de données
    writer.writerows(data)

print(f"Fichier 'salaires.csv' généré avec succès ! ({len(data)} lignes créées)")