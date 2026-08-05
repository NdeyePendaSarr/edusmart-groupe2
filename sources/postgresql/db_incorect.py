import psycopg2
from faker import Faker
import random
import uuid
from datetime import datetime, timedelta

# ======================================================
# Configuration Faker
# ======================================================
fake = Faker("fr_FR")

# ======================================================
# Connexion PostgreSQL
# ======================================================
conn = psycopg2.connect(
    host="localhost",
    database="edusmart_academic",
    user="postgres",
    password="",
    port=5432
)

cur = conn.cursor()

print("===== Nettoyage de la base =====")

cur.execute("""
DROP TABLE IF EXISTS paiements CASCADE;
DROP TABLE IF EXISTS inscriptions CASCADE;
DROP TABLE IF EXISTS classes CASCADE;
DROP TABLE IF EXISTS filieres CASCADE;
DROP TABLE IF EXISTS etudiants CASCADE;
""")

cur.execute("""
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
""")

print("===== Création des tables =====")

cur.execute("""

CREATE TABLE etudiants(
    id_etudiant UUID PRIMARY KEY,
    matricule VARCHAR(50),
    nom VARCHAR(100),
    prenom VARCHAR(100),
    sexe VARCHAR(20),
    date_naissance DATE,
    telephone VARCHAR(50),
    email VARCHAR(150),
    adresse TEXT,
    ville VARCHAR(100),
    region VARCHAR(100),
    pays VARCHAR(100),
    date_creation TIMESTAMP
);

CREATE TABLE filieres(
    id_filiere UUID PRIMARY KEY,
    code_filiere VARCHAR(20),
    nom_filiere VARCHAR(150),
    departement VARCHAR(100),
    niveau VARCHAR(30),
    duree_mois INTEGER,
    cout_total NUMERIC(12,2),
    statut VARCHAR(20)
);

CREATE TABLE classes(
    id_classe UUID PRIMARY KEY,
    code_classe VARCHAR(30),
    nom_classe VARCHAR(100),
    id_filiere UUID,
    annee_academique VARCHAR(20),
    capacite INTEGER,
    salle VARCHAR(50),
    responsable VARCHAR(100)
);

CREATE TABLE inscriptions(
    id_inscription UUID PRIMARY KEY,
    id_etudiant UUID,
    id_classe UUID,
    date_inscription DATE,
    statut VARCHAR(30),
    type_inscription VARCHAR(30),
    bourse BOOLEAN,
    reduction NUMERIC(5,2)
);

CREATE TABLE paiements(
    id_paiement UUID PRIMARY KEY,
    id_inscription UUID,
    reference VARCHAR(50),
    date_paiement DATE,
    montant NUMERIC(12,2),
    mode_paiement VARCHAR(50),
    statut VARCHAR(30),
    tranche VARCHAR(20)
);

""")

print("Tables créées avec succès.")

print("===== Génération des filières =====")

filieres_data = [
    (str(uuid.uuid4()), "DD003", "Développement Data", "Data & IA", "Doctorat", 24, 900000, "ACTIF"),
    (str(uuid.uuid4()), "DW002", "Développement Web", "Développement", "Master", 24, 750000, "ACTIF"),
    (str(uuid.uuid4()), "DM002", "Développement Mobile", "Développement", "Master", 36, 850000, "ACTIF"),
    (str(uuid.uuid4()), "CS003", "Cybersécurité", "Sécurité", "Doctorat", 24, 950000, "ACTIF"),
    (str(uuid.uuid4()), "CD002", "Cloud & DevOps", "Infrastructure", "Master", 36, 1000000, "ACTIF"),
    (str(uuid.uuid4()), "UX001", "UX/UI Design", "Design", "Licence", 36, 700000, "ACTIF"),
    (str(uuid.uuid4()), "GP002", "Gestion de Projet IT", "Management", "Master", 36, 650000, "ACTIF"),
    (str(uuid.uuid4()), "IA003", "Intelligence Artificielle", "Data & IA", "Doctorat", 12, 1500000, "ACTIF"),
    (str(uuid.uuid4()), "IA002", "IA", "Data & IA", "Master", 12, 190000, "ACTIF"),
    (str(uuid.uuid4()), "INFO01", "Informatique", "Sciences et Technologies", "Licence", 36, 1500000, "ACTIF"),
    (str(uuid.uuid4()), "GEST02", "Gestion", "Sciences Economiques", "Licence", 36, 1200000, "ACTIF"),
    (str(uuid.uuid4()), "IA01", "Ingénierie IA", "Informatique", "Licence", 36, 500000, "INACTIF"),
    (str(uuid.uuid4()), "IA02", "IA Advanced", "Informatique", "Master", 120, 1850000, "INACTIF"),
]

cur.executemany("""
INSERT INTO filieres
(id_filiere,code_filiere,nom_filiere,departement,niveau,duree_mois,cout_total,statut)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
""", filieres_data)

conn.commit()

cur.execute("SELECT id_filiere,code_filiere FROM filieres")
filieres = cur.fetchall()

filiere_map = {code:idf for idf,code in filieres}

print("===== Génération des classes =====")

classes_data=[]

for i in range(10):

    id_classe=str(uuid.uuid4())

    if random.random()<0.20:
        id_filiere=str(uuid.uuid4())
    else:
        code=random.choice(list(filiere_map.keys()))
        id_filiere=filiere_map[code]

    classes_data.append((
        id_classe,
        f"CL{i+1:03}",
        f"Classe {i+1}",
        id_filiere,
        random.choice(["2024-2025","2025-2026","2024/2025"]),
        random.choice([10,30,45,50,500]),
        random.choice([f"Salle A{100+i}",f"A{100+i}",f"A-{100+i}",f"B{200+i}"]),
        fake.name()
    ))

cur.executemany("""
INSERT INTO classes
(id_classe,code_classe,nom_classe,id_filiere,annee_academique,capacite,salle,responsable)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
""", classes_data)

conn.commit()

cur.execute("SELECT id_classe FROM classes")
class_ids=[x[0] for x in cur.fetchall()]

print("===== Génération des étudiants =====")

regions={
    "Dakar": ["Pikine", "Guédiawaye", "Rufisque", "Mbour", "Sangalkam", "Diamniadio"],
    "Thiès": ["Thiès", "Tivaouane", "Mbour", "Kayar", "Meckhe"],
    "Saint-Louis": ["Dagana", "Podor"],
    "Kaolack": ["Nioro du Rip", "Guinguinéo"],
    "Ziguinchor": ["Bignona", "Oussouye"],
    "Kolda": ["Vélingara", "Sédhiou"],
    "Tambacounda": ["Goudomp", "Bakel"],
    "Fatick": ["Foundiougne", "Gossas"],
    "Louga": ["Kébémer", "Linguère"],
    "Matam": ["Kanel", "Ourossogui"],
    "Diourbel": ["Mbacké", "Touba"],
    "Kédougou": ["Salémata"],
    "kaffrine": ["Malem Hodar", "Birkelane"],
    "Sédhiou": ["Bounkiling", "Goudomp"]
}

etudiants_data=[]

for i in range(15000):

    id_etudiant=str(uuid.uuid4())

    matricule="ETU1000" if random.random()<0.10 else f"ETU{i+1000:05}"

    nom=fake.last_name()

    prenom=fake.first_name()

    sexe=random.choice(["M","F","Homme","Femme","1","0","Masculin",None])

    if random.random()<0.10:
        naissance=datetime.now()+timedelta(days=365)
    else:
        naissance=fake.date_of_birth(minimum_age=18,maximum_age=30)

    if random.random()<0.10:
        telephone=""
    else:
        telephone=random.choice([
            "77","78","76","70","+22177","+22178","0022177"
        ])+"".join(random.choices("0123456789",k=7))

    region=random.choice(list(regions.keys()))
    ville=random.choice(regions[region])

    etudiants_data.append((
        id_etudiant,
        matricule,
        nom,
        prenom,
        sexe,
        naissance,
        telephone,
        fake.email(),
        fake.address(),
        ville,
        region,
        "Sénégal",
        datetime.now()
    ))

cur.executemany("""
INSERT INTO etudiants
(id_etudiant,matricule,nom,prenom,sexe,date_naissance,telephone,email,adresse,ville,region,pays,date_creation)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
""",etudiants_data)

conn.commit()

cur.execute("SELECT id_etudiant FROM etudiants")
etudiant_ids=[x[0] for x in cur.fetchall()]

print("===== Génération des inscriptions =====")

inscriptions=[]

for i in range(14905):

    id_ins=str(uuid.uuid4())

    id_et=str(uuid.uuid4()) if random.random()<0.15 else random.choice(etudiant_ids)

    id_cl=random.choice(class_ids)

    date_ins=fake.date_between(start_date="-2y",end_date="today")

    if random.random()<0.10:
        date_ins=date_ins+timedelta(days=500)

    inscriptions.append((
        id_ins,
        id_et,
        id_cl,
        date_ins,
        random.choice(["INSCRIT","EN ATTENTE","ANNULE","UNKNOWN"]),
        random.choice(["Nouvelle","Reinscription","Reinscription ","NOUVELLE",None]),
        random.choice([True,False,None]),
        random.choice([0,10,25,150,-20])
    ))

cur.executemany("""
INSERT INTO inscriptions
(id_inscription,id_etudiant,id_classe,date_inscription,statut,type_inscription,bourse,reduction)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
""",inscriptions)

conn.commit()

cur.execute("SELECT id_inscription FROM inscriptions")
inscription_ids=[x[0] for x in cur.fetchall()]

print("===== Génération des paiements =====")

modes=[
"Espèces",
"OM",
"Orange Money",
"orange money",
"Wave",
"Virement",
"Chèque"
]

paiements=[]

for i in range(14907):

    paiements.append((
        str(uuid.uuid4()),
        str(uuid.uuid4()) if random.random()<0.20 else random.choice(inscription_ids),
        "REF_DOUBLON_123" if random.random()<0.10 else fake.bothify("REF########"),
        fake.date_between(start_date="-2y",end_date="today"),
        random.choice([10000,50000,-15000,0,15000000]),
        random.choice(modes),
        random.choice(["VALIDE","ECHEC","REFUSE",None]),
        random.choice(["1ere","2eme","3eme","Tranche 1","1"])
    ))

cur.executemany("""
INSERT INTO paiements
(id_paiement,id_inscription,reference,date_paiement,montant,mode_paiement,statut,tranche)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
""",paiements)

conn.commit()

print("Toutes les données ont été générées avec succès.")