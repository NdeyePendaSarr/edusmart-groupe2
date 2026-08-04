"""
=============================================================================
 extract_mysql.py
 EduSmart Decision Platform - Source 2 (MySQL) - v2 (equipe MySQL)
=============================================================================

Description
-----------
Extrait les 6 tables de la base MySQL edusmart_learning_v2 vers des fichiers
CSV places dans data/staging/. Ces CSV seront consommes par le pipeline ETL
commun (transform.py + load.py, a livrer lors de la prochaine session).

Ce script est le premier maillon operationnel du pipeline BI.

Fondamentaux
------------
- Extraction par batch de 5 000 lignes (economie memoire)
- Logging structure (fichier + console)
- Metadonnees d'extraction produites dans un JSON pour la Phase 6
- Identifiants MySQL charges depuis .env (jamais hardcodes)
- Gestion des erreurs par table (une erreur n'interrompt pas les autres)
- Code de sortie 0 (succes) ou 1 (au moins une erreur)

Conventions de sortie (partagees avec les autres extract_*.py de l'equipe)
-------------------------------------------------------------------------
- Prefixe : mysql_ (pour identifier la source)
- Format  : CSV avec separateur virgule, encodage UTF-8, quoting minimal
- Dossier : data/staging/
- Metadonnees : data/staging/metadata_extract_mysql.json

Utilisation
-----------
    python extract_mysql.py

=============================================================================
"""

import csv
import json
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

SOURCE_NAME = "mysql"
DATABASE_NAME = "edusmart_learning_v2"

# Tables a extraire (ordre logique : catalogue puis activite)
TABLES_TO_EXTRACT = [
    "modules",
    "cours",
    "quiz",
    "notes",
    "progression",
    "temps_connexion",
]

# Chemins
BASE_DIR = Path(__file__).resolve().parent
STAGING_DIR = BASE_DIR / "data" / "staging"
LOGS_DIR = BASE_DIR / "logs"
METADATA_FILE = STAGING_DIR / f"metadata_extract_{SOURCE_NAME}.json"

# Batch d'extraction
BATCH_SIZE = 5000

# =============================================================================
# INITIALISATION
# =============================================================================

STAGING_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / f"extract_{SOURCE_NAME}.log", mode="w", encoding="utf-8"),
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
        "database": os.getenv("MYSQL_DATABASE", DATABASE_NAME),
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
    }


def connect_to_mysql():
    config = get_mysql_config()
    logger.info("Connexion : %s@%s:%s/%s",
                config["user"], config["host"], config["port"], config["database"])
    conn = mysql.connector.connect(**config)
    logger.info("Connexion etablie.")
    return conn


# =============================================================================
# EXTRACTION D'UNE TABLE
# =============================================================================

def normalize_value(value):
    """
    Convertit une valeur MySQL vers un format CSV portable.

    - None -> chaine vide (NULL)
    - datetime -> format ISO YYYY-MM-DD HH:MM:SS
    - autres -> str(value)
    """
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


def extract_table(conn, table_name):
    """
    Extrait une table complete vers un fichier CSV.

    Retourne un dictionnaire avec les metadonnees de l'extraction.
    """
    logger.info("--- Extraction de la table : %s ---", table_name)
    start_time = time.time()

    output_file = STAGING_DIR / f"{SOURCE_NAME}_{table_name}.csv"

    result = {
        "table": table_name,
        "rows_extracted": 0,
        "columns": [],
        "output_file": str(output_file),
        "duration_seconds": 0,
        "status": "success",
        "error_message": None,
    }

    try:
        # Curseur en mode dictionnaire
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name}")

        # Recupere les noms de colonnes
        columns = [desc[0] for desc in cursor.description]
        result["columns"] = columns

        # Ecriture du CSV
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=columns,
                delimiter=",",
                quoting=csv.QUOTE_MINIMAL,
                lineterminator="\n",
            )
            writer.writeheader()

            row_count = 0
            while True:
                rows = cursor.fetchmany(BATCH_SIZE)
                if not rows:
                    break

                normalized_rows = [
                    {col: normalize_value(row[col]) for col in columns}
                    for row in rows
                ]
                writer.writerows(normalized_rows)
                row_count += len(rows)

                if row_count % 100000 == 0:
                    logger.info("    ... %d lignes extraites", row_count)

        cursor.close()

        result["rows_extracted"] = row_count
        result["duration_seconds"] = round(time.time() - start_time, 2)
        logger.info("    %s : %d lignes extraites en %.2fs -> %s",
                    table_name, row_count, result["duration_seconds"],
                    output_file.name)

    except mysql.connector.Error as e:
        result["status"] = "error"
        result["error_message"] = f"MySQL error: {e}"
        result["duration_seconds"] = round(time.time() - start_time, 2)
        logger.error("    Echec extraction %s : %s", table_name, e)

    except Exception as e:
        result["status"] = "error"
        result["error_message"] = f"{type(e).__name__}: {e}"
        result["duration_seconds"] = round(time.time() - start_time, 2)
        logger.error("    Erreur inattendue sur %s : %s", table_name, e)

    return result


# =============================================================================
# METADONNEES
# =============================================================================

def write_metadata(results, total_duration):
    """Ecrit un fichier JSON avec les metadonnees de l'extraction."""
    metadata = {
        "source": SOURCE_NAME,
        "database": DATABASE_NAME,
        "extraction_timestamp": datetime.now().isoformat(),
        "total_duration_seconds": round(total_duration, 2),
        "tables": results,
        "summary": {
            "tables_total": len(results),
            "tables_success": sum(1 for r in results if r["status"] == "success"),
            "tables_failed": sum(1 for r in results if r["status"] == "error"),
            "rows_total": sum(r["rows_extracted"] for r in results),
        },
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info("Metadonnees ecrites : %s", METADATA_FILE.name)


# =============================================================================
# ORCHESTRATION
# =============================================================================

def main():
    logger.info("=" * 70)
    logger.info("EXTRACTION DE LA SOURCE MYSQL")
    logger.info("=" * 70)
    logger.info("Source : %s (%s)", SOURCE_NAME, DATABASE_NAME)
    logger.info("Tables : %s", ", ".join(TABLES_TO_EXTRACT))
    logger.info("Sortie : %s", STAGING_DIR)
    logger.info("")

    global_start = time.time()

    try:
        conn = connect_to_mysql()
    except mysql.connector.Error as e:
        logger.error("Impossible de se connecter : %s", e)
        return 1

    results = []
    try:
        for table_name in TABLES_TO_EXTRACT:
            result = extract_table(conn, table_name)
            results.append(result)
            logger.info("")
    finally:
        conn.close()
        logger.info("Connexion fermee.")
        logger.info("")

    total_duration = time.time() - global_start
    write_metadata(results, total_duration)

    logger.info("=" * 70)
    logger.info("BILAN DE L'EXTRACTION")
    logger.info("=" * 70)

    nb_success = 0
    nb_failed = 0
    total_rows = 0
    for r in results:
        symbol = "OK" if r["status"] == "success" else "KO"
        logger.info("  [%s] %-18s : %8d lignes en %6.2fs",
                    symbol, r["table"], r["rows_extracted"],
                    r["duration_seconds"])
        total_rows += r["rows_extracted"]
        if r["status"] == "success":
            nb_success += 1
        else:
            nb_failed += 1

    logger.info("-" * 70)
    logger.info("  TOTAL : %d tables (%d OK, %d KO) - %d lignes en %.2fs",
                len(results), nb_success, nb_failed, total_rows, total_duration)
    logger.info("=" * 70)

    exit_code = 0 if nb_failed == 0 else 1
    logger.info("Extraction terminee. Code de sortie : %d", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
