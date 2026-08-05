import psycopg2
import pandas as pd
import os

# Connexion à PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="edusmart_academic",
    user="postgres",
    password="",
    port=5432
)

# Dossier où enregistrer les fichiers CSV
output_dir = "regroupement/data"
os.makedirs(output_dir, exist_ok=True)

# Liste de tes tables
tables = ['etudiants', 'filieres', 'classes', 'inscriptions', 'paiements']

# 2. Boucle pour exporter chaque table en CSV
for table in tables:
    print(f"Exportation de la table '{table}'...")
    df = pd.read_sql_query(f"SELECT * FROM {table};", conn)

    file_path = os.path.join(output_dir, f"{table}.csv")
    df.to_csv(file_path, index=False, encoding='utf-8-sig') # utf-8-sig pour compatibilité Excel
    print(f"-> Enregistré : {file_path}")

conn.close()
print("\n Tous les fichiers CSV ont été générés avec succès dans le dossier 'csv_exports' !")
