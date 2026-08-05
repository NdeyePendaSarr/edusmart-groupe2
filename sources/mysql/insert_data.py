"""
=============================================================================
 insert_data.py
 EduSmart Decision Platform - Source 2 (MySQL) - v2 (equipe MySQL)
=============================================================================

Description
-----------
Charge les 6 fichiers CSV partages sur le Drive dans la base MySQL
edusmart_learning_v2.

Ce script NE GENERE PAS de donnees : il ne fait que charger les CSV existants.
La coherence des donnees entre les 5 membres de l'equipe MySQL est ainsi
garantie (tout le monde part des memes CSV).

Fondamentaux
------------
- Les CSV doivent etre places dans data/input/ (modules.csv, cours.csv,
  quiz.csv, notes.csv, progression.csv, temps_connexion.csv).
- Separateur CSV : point-virgule (;)
- Encodage : UTF-8 (avec ou sans BOM)
- Ordre de chargement : modules -> cours -> quiz -> notes/progression/
  temps_connexion (dependances FK).
- Insertion par batch de 5 000 lignes pour la performance.
- Desactivation temporaire de FOREIGN_KEY_CHECKS pendant l'insertion
  (car progression contient des id_module fantomes volontaires).

Utilisation
-----------
    python insert_data.py

Prerequis
---------
1. Base creee : mysql -u root -p < create_database.sql
2. Fichier .env avec les identifiants MySQL (copier .env.example)
3. Les 6 CSV places dans data/input/

Sortie
------
- La base est peuplee.
- Un fichier logs/insert_data.log est produit avec le detail.
- Un rapport de bilan est affiche a la fin.

=============================================================================
"""

import csv
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# =============================================================================
# CONFIGURATION
# =============================================================================

# Chemins
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "data" / "input"
LOGS_DIR = BASE_DIR / "logs"

# Fichiers CSV attendus (ordre = ordre d'insertion respectant les FK)
CSV_FILES = [
    ("modules.csv", "modules"),
    ("cours.csv", "cours"),
    ("quiz.csv", "quiz"),
    ("notes.csv", "notes"),
    ("progression.csv", "progression"),
    ("temps_connexion.csv", "temps_connexion"),
]

# Batch d'insertion
BATCH_SIZE = 5000

# Colonnes attendues par table (dans l'ordre du CSV)
TABLE_COLUMNS = {
    "modules": ["id_module", "code_module", "nom_module", "categorie",
                "niveau", "duree_heures", "actif"],
    "cours": ["id_cours", "id_module", "titre", "ordre",
              "duree_minutes", "type_cours", "statut"],
    "quiz": ["id_quiz", "id_cours", "titre", "nb_questions",
             "score_max", "duree_minutes"],
    "notes": ["id_note", "id_quiz", "student_code", "date_passage",
              "score", "tentative", "valide"],
    "progression": ["id_progression", "student_code", "id_module",
                    "pourcentage", "dernier_cours", "date_maj"],
    "temps_connexion": ["id_connexion", "student_code", "date_connexion",
                        "date_deconnexion", "duree_minutes", "appareil",
                        "navigateur", "adresse_ip"],
}

# =============================================================================
# INITIALISATION
# =============================================================================

LOGS_DIR.mkdir(parents=True, exist_ok=True)
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "insert_data.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONNEXION MYSQL
# =============================================================================

def get_mysql_config():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "edusmart_user"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "edusmart_learning_v2"),
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        # Pour supporter des chaines de 500 000 lignes lors des executemany
        "allow_local_infile": True,
    }


def connect_to_mysql():
    config = get_mysql_config()
    logger.info("Connexion : %s@%s:%s/%s",
                config["user"], config["host"], config["port"], config["database"])
    conn = mysql.connector.connect(**config)
    logger.info("Connexion etablie.")
    return conn


# =============================================================================
# HELPERS DE CONVERSION
# =============================================================================

def parse_value(value, column_name):
    """
    Convertit une valeur CSV en type Python adapte a l'insertion MySQL.

    Regles :
    - Chaine vide -> None (NULL en base)
    - Booleens '0'/'1' ou 'True'/'False' -> True/False
    - Numeriques laisses en str (MySQL convertit automatiquement)
    - Dates laissees en str (MySQL parse le format 'YYYY-MM-DD HH:MM:SS')
    """
    if value is None or value == "":
        return None

    # Colonnes booleennes
    if column_name in ("actif", "valide"):
        if value in ("1", "True", "true", "TRUE"):
            return True
        if value in ("0", "False", "false", "FALSE"):
            return False
        return None

    return value


def read_csv(filepath):
    """
    Lit un CSV avec le separateur point-virgule et retourne la liste des lignes.

    Le CSV est lu avec encodage utf-8-sig pour absorber un eventuel BOM.
    """
    rows = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            rows.append(row)
    return rows


# =============================================================================
# INSERTION D'UNE TABLE
# =============================================================================

def insert_table(conn, csv_filename, table_name):
    """
    Insere le contenu d'un CSV dans une table MySQL.

    Retourne un dictionnaire avec les metadonnees :
        {
            "table": nom de la table,
            "rows_inserted": nombre de lignes inserees,
            "rows_failed": nombre de lignes en echec,
            "duration_seconds": duree,
            "status": "success" | "partial" | "error"
        }
    """
    logger.info("--- Insertion de %s ---", table_name)
    start_time = time.time()

    result = {
        "table": table_name,
        "csv_file": csv_filename,
        "rows_inserted": 0,
        "rows_failed": 0,
        "duration_seconds": 0,
        "status": "success",
        "error_message": None,
    }

    filepath = INPUT_DIR / csv_filename
    if not filepath.exists():
        result["status"] = "error"
        result["error_message"] = f"Fichier {filepath} introuvable"
        logger.error("  Fichier %s introuvable. Placer les CSV dans data/input/", filepath)
        return result

    columns = TABLE_COLUMNS[table_name]
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

    try:
        rows = read_csv(filepath)
        logger.info("  Lignes lues depuis %s : %d", csv_filename, len(rows))

        cursor = conn.cursor()
        batch = []

        for row in rows:
            # Preparer les valeurs dans l'ordre des colonnes
            values = tuple(parse_value(row.get(col, ""), col) for col in columns)
            batch.append(values)

            if len(batch) >= BATCH_SIZE:
                try:
                    cursor.executemany(sql, batch)
                    conn.commit()
                    result["rows_inserted"] += len(batch)
                except mysql.connector.Error as e:
                    # Un batch a echoue : on essaie ligne par ligne pour identifier
                    conn.rollback()
                    logger.warning("  Batch echoue, essai ligne par ligne : %s", e)
                    for values in batch:
                        try:
                            cursor.execute(sql, values)
                            conn.commit()
                            result["rows_inserted"] += 1
                        except mysql.connector.Error as e2:
                            result["rows_failed"] += 1
                            if result["rows_failed"] <= 5:
                                logger.warning("    Ligne echouee : %s", e2)
                batch = []

                if result["rows_inserted"] % 100000 == 0 and result["rows_inserted"] > 0:
                    logger.info("    ... %d lignes inserees", result["rows_inserted"])

        # Dernier batch
        if batch:
            try:
                cursor.executemany(sql, batch)
                conn.commit()
                result["rows_inserted"] += len(batch)
            except mysql.connector.Error as e:
                conn.rollback()
                logger.warning("  Dernier batch echoue, essai ligne par ligne : %s", e)
                for values in batch:
                    try:
                        cursor.execute(sql, values)
                        conn.commit()
                        result["rows_inserted"] += 1
                    except mysql.connector.Error as e2:
                        result["rows_failed"] += 1

        cursor.close()

        if result["rows_failed"] > 0:
            result["status"] = "partial"

        result["duration_seconds"] = round(time.time() - start_time, 2)
        logger.info("  %s : %d inserees, %d echouees en %.2fs",
                    table_name, result["rows_inserted"], result["rows_failed"],
                    result["duration_seconds"])

    except Exception as e:
        result["status"] = "error"
        result["error_message"] = f"{type(e).__name__}: {e}"
        result["duration_seconds"] = round(time.time() - start_time, 2)
        logger.error("  Erreur lors de l'insertion de %s : %s", table_name, e)

    return result


# =============================================================================
# ORCHESTRATION
# =============================================================================

def main():
    logger.info("=" * 70)
    logger.info("CHARGEMENT DES CSV DU DRIVE DANS edusmart_learning_v2")
    logger.info("=" * 70)
    logger.info("Dossier d'entree : %s", INPUT_DIR)
    logger.info("")

    # Verifier que tous les CSV sont presents
    missing = []
    for csv_filename, _ in CSV_FILES:
        if not (INPUT_DIR / csv_filename).exists():
            missing.append(csv_filename)
    if missing:
        logger.error("Fichiers CSV manquants dans data/input/ :")
        for m in missing:
            logger.error("  - %s", m)
        logger.error("Telecharger tous les CSV depuis le Drive avant de continuer.")
        return 1

    global_start = time.time()

    # Connexion
    conn = connect_to_mysql()

    try:
        # Desactivation des FK pour permettre le chargement dans n'importe quel ordre
        # et pour absorber les eventuels id_module fantomes de progression.
        cursor = conn.cursor()
        logger.info("Desactivation temporaire de FOREIGN_KEY_CHECKS...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.close()

        # Insertion table par table
        results = []
        for csv_filename, table_name in CSV_FILES:
            result = insert_table(conn, csv_filename, table_name)
            results.append(result)
            logger.info("")

        # Reactivation des FK
        cursor = conn.cursor()
        logger.info("Reactivation de FOREIGN_KEY_CHECKS...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        cursor.close()

    finally:
        conn.close()
        logger.info("Connexion fermee.")
        logger.info("")

    # Bilan
    total_duration = time.time() - global_start
    logger.info("=" * 70)
    logger.info("BILAN DU CHARGEMENT")
    logger.info("=" * 70)

    total_inserted = 0
    total_failed = 0
    nb_success = 0
    nb_partial = 0
    nb_error = 0

    for r in results:
        symbol = {"success": "OK", "partial": "!!", "error": "KO"}.get(r["status"], "??")
        logger.info(
            "  [%s] %-18s : %7d inserees, %6d echouees en %6.2fs",
            symbol, r["table"], r["rows_inserted"], r["rows_failed"], r["duration_seconds"]
        )
        total_inserted += r["rows_inserted"]
        total_failed += r["rows_failed"]
        if r["status"] == "success":
            nb_success += 1
        elif r["status"] == "partial":
            nb_partial += 1
        else:
            nb_error += 1

    logger.info("-" * 70)
    logger.info(
        "  TOTAL : %d tables (%d OK, %d partiel, %d KO) - %d lignes inserees en %.2fs",
        len(results), nb_success, nb_partial, nb_error, total_inserted, total_duration
    )
    if total_failed > 0:
        logger.warning("  %d lignes en echec au total (voir logs pour details)", total_failed)
    logger.info("=" * 70)

    # Code de sortie
    exit_code = 0 if nb_error == 0 else 1
    logger.info("Chargement termine. Code de sortie : %d", exit_code)
    logger.info("Etape suivante : lancer python test_data_quality.py")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
