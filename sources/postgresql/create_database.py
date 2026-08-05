import psycopg2

# Configuration PostgreSQL
DB_CONFIG = {
    "host": "localhost",
    "database": "edusmart_academic",
    "user": "postgres",
    "password": "",
    "port": 5432
}


def create_tables():

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("Création des tables PostgreSQL...")


    cursor.execute("""
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


    CREATE TABLE IF NOT EXISTS filieres(
        id_filiere UUID PRIMARY KEY,
        code_filiere VARCHAR(20),
        nom_filiere VARCHAR(150),
        departement VARCHAR(100),
        niveau VARCHAR(30),
        duree_mois INTEGER,
        cout_total NUMERIC(12,2),
        statut VARCHAR(20)
    );


    CREATE TABLE IF NOT EXISTS classes(
        id_classe UUID PRIMARY KEY,
        code_classe VARCHAR(30),
        nom_classe VARCHAR(100),
        id_filiere UUID,
        annee_academique VARCHAR(20),
        capacite INTEGER,
        salle VARCHAR(50),
        responsable VARCHAR(100),

        CONSTRAINT fk_classe_filiere
        FOREIGN KEY(id_filiere)
        REFERENCES filieres(id_filiere)
    );


    CREATE TABLE IF NOT EXISTS etudiants(
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


    CREATE TABLE IF NOT EXISTS inscriptions(
        id_inscription UUID PRIMARY KEY,
        id_etudiant UUID,
        id_classe UUID,
        date_inscription DATE,
        statut VARCHAR(30),
        type_inscription VARCHAR(30),
        bourse BOOLEAN,
        reduction NUMERIC(5,2),

        CONSTRAINT fk_inscription_etudiant
        FOREIGN KEY(id_etudiant)
        REFERENCES etudiants(id_etudiant),

        CONSTRAINT fk_inscription_classe
        FOREIGN KEY(id_classe)
        REFERENCES classes(id_classe)
    );


    CREATE TABLE IF NOT EXISTS paiements(
        id_paiement UUID PRIMARY KEY,
        id_inscription UUID,
        reference VARCHAR(50),
        date_paiement DATE,
        montant NUMERIC(12,2),
        mode_paiement VARCHAR(50),
        statut VARCHAR(30),
        tranche VARCHAR(20),

        CONSTRAINT fk_paiement_inscription
        FOREIGN KEY(id_inscription)
        REFERENCES inscriptions(id_inscription)
    );
    """)


    conn.commit()

    cursor.close()
    conn.close()

    print("Tables créées avec succès.")


if __name__ == "__main__":
    create_tables()