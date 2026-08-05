import psycopg2
import pandas as pd
import os

# ==============================
# Configuration PostgreSQL
# ==============================

DB_CONFIG = {
    "host": "localhost",
    "database": "edusmart_academic",
    "user": "postgres",
    "password": "Pensarr12",
    "port": 5432
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "input")


# ==============================
# Connexion
# ==============================

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# ==============================
# Chargement CSV
# ==============================

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)

    print(f"Lecture de {filename}...")

    return pd.read_csv(
        path,
        encoding="utf-8",
        dtype=str
    )


# ==============================
# Insertion table
# ==============================

def insert_dataframe(conn, table, df):

    cursor = conn.cursor()

    columns = list(df.columns)

    cols = ",".join(columns)

    placeholders = ",".join(["%s"] * len(columns))

    query = f"""
        INSERT INTO {table}
        ({cols})
        VALUES ({placeholders})
    """

    data = [
        tuple(None if pd.isna(x) else x for x in row)
        for row in df.values
    ]

    print(f"Insertion {table} : {len(data)} lignes")

    cursor.executemany(query, data)

    conn.commit()

    cursor.close()

    print(f"✓ {table} terminé")


# ==============================
# Programme principal
# ==============================

def main():

    conn = get_connection()

    try:

        fichiers = [
            ("filieres.csv", "filieres"),
            ("classes.csv", "classes"),
            ("etudiants.csv", "etudiants"),
            ("inscriptions.csv", "inscriptions"),
            ("paiements.csv", "paiements")
        ]


        for fichier, table in fichiers:

            df = load_csv(fichier)

            insert_dataframe(
                conn,
                table,
                df
            )


        print("\n================================")
        print("Chargement PostgreSQL terminé !")
        print("================================")


    except Exception as e:

        conn.rollback()

        print("\nErreur pendant l'insertion :")
        print(e)

    finally:

        conn.close()


if __name__ == "__main__":
    main()