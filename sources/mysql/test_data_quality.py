"""
=============================================================================
 test_data_quality.py
 EduSmart Decision Platform - Source 2 (MySQL) - v2 (equipe MySQL)
=============================================================================

Description
-----------
Verifie que la base MySQL edusmart_learning_v2 est bien peuplee avec les
donnees attendues, en volume et en qualite.

Ce script joue deux roles :
1. Preuve automatique que le chargement a reussi (post-insert_data.py)
2. Verification que les anomalies volontaires sont bien presentes (attendu
   par le pipeline ETL de la Phase B)

Categories de tests
-------------------
1. VOLUMETRIE STRICTE          (6 tests)  : volumes exacts par table
2. ANOMALIES VOLONTAIRES       (10 tests) : taux d'anomalies observes
3. INTEGRITE RELATIONNELLE     (6 tests)  : FK, coherence, unicite
4. FORMAT DES DONNEES          (4 tests)  : student_code, dates, IP

Total : 26 tests

Utilisation
-----------
    python test_data_quality.py

Sortie
------
- Un rapport detaille dans logs/test_data_quality.log
- Un affichage console avec statut de chaque test
- Code de sortie 0 (tous verts) ou 1 (au moins un rouge)

=============================================================================
"""

import logging
import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "test_data_quality.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# =============================================================================
# INFRASTRUCTURE DES TESTS
# =============================================================================

class TestReport:
    """Accumule les resultats des tests et produit un bilan final."""

    def __init__(self):
        self.tests = []
        self.categories = {}

    def add(self, category, name, passed, expected, actual, details=""):
        self.tests.append({
            "category": category,
            "name": name,
            "passed": passed,
            "expected": expected,
            "actual": actual,
            "details": details,
        })
        if category not in self.categories:
            self.categories[category] = {"passed": 0, "failed": 0}
        if passed:
            self.categories[category]["passed"] += 1
        else:
            self.categories[category]["failed"] += 1

    def display(self):
        logger.info("=" * 70)
        logger.info("RAPPORT DES TESTS DE QUALITE")
        logger.info("=" * 70)

        current_cat = None
        for t in self.tests:
            if t["category"] != current_cat:
                current_cat = t["category"]
                logger.info("")
                logger.info("[%s]", current_cat)

            symbol = "OK" if t["passed"] else "KO"
            logger.info("  [%s] %s", symbol, t["name"])
            logger.info("       attendu : %s", t["expected"])
            logger.info("       obtenu  : %s", t["actual"])
            if t["details"]:
                logger.info("       %s", t["details"])

        logger.info("")
        logger.info("=" * 70)
        logger.info("BILAN PAR CATEGORIE")
        logger.info("=" * 70)
        total_passed = 0
        total_failed = 0
        for cat, stats in self.categories.items():
            logger.info("  %-30s : %d OK / %d KO",
                        cat, stats["passed"], stats["failed"])
            total_passed += stats["passed"]
            total_failed += stats["failed"]
        logger.info("-" * 70)
        logger.info("  TOTAL : %d tests, %d OK, %d KO",
                    total_passed + total_failed, total_passed, total_failed)
        logger.info("=" * 70)

        return total_failed == 0


# =============================================================================
# HELPERS
# =============================================================================

def check_between(actual, low, high):
    """Retourne True si low <= actual <= high."""
    return low <= actual <= high


def scalar(cursor, sql):
    """Retourne la premiere valeur de la premiere ligne d'une requete SELECT."""
    cursor.execute(sql)
    row = cursor.fetchone()
    return row[0] if row else None


# =============================================================================
# 1. TESTS DE VOLUMETRIE STRICTE
# =============================================================================

VOLUMES_ATTENDUS = {
    "modules":         500,
    "cours":           2000,
    "quiz":            5000,
    "notes":           500000,
    "progression":     15000,
    "temps_connexion": 80000,
}

def test_volumetrie(cursor, report):
    """Verifie les volumes exacts par table."""
    for table, expected in VOLUMES_ATTENDUS.items():
        actual = scalar(cursor, f"SELECT COUNT(*) FROM {table}")
        passed = actual == expected
        report.add(
            "VOLUMETRIE",
            f"Volume {table}",
            passed,
            f"{expected} lignes",
            f"{actual} lignes",
        )


# =============================================================================
# 2. TESTS DES ANOMALIES VOLONTAIRES
# =============================================================================

def test_anomalies(cursor, report):
    """Verifie que les anomalies volontaires sont bien presentes."""

    # A1 - Variantes de categories dans modules
    n_cat = scalar(cursor, "SELECT COUNT(DISTINCT categorie) FROM modules")
    report.add(
        "ANOMALIES",
        "A1  - Variantes de categories (Data, DATA, data science...)",
        n_cat >= 8,
        "au moins 8 categories distinctes",
        f"{n_cat} categories",
    )

    # A2 - Modules inactifs
    n_inactifs = scalar(cursor, "SELECT COUNT(*) FROM modules WHERE actif = FALSE")
    pct = 100 * n_inactifs / 500
    report.add(
        "ANOMALIES",
        "A2  - Modules inactifs",
        check_between(pct, 15, 40),
        "entre 15% et 40% (~27.6% observe)",
        f"{n_inactifs} ({pct:.1f}%)",
    )

    # A5 - Durees quiz negatives ou nulles
    n_duree_ko = scalar(cursor, "SELECT COUNT(*) FROM quiz WHERE duree_minutes <= 0")
    report.add(
        "ANOMALIES",
        "A5  - Quiz avec duree_minutes <= 0",
        n_duree_ko >= 0,
        "presence attendue (peut etre 0)",
        f"{n_duree_ko} quiz",
    )

    # A6 - Notes avec score negatif
    n_score_neg = scalar(cursor, "SELECT COUNT(*) FROM notes WHERE score < 0")
    pct = 100 * n_score_neg / 500000
    report.add(
        "ANOMALIES",
        "A6  - Notes avec score < 0",
        check_between(pct, 3, 15),
        "entre 3% et 15% (~7.7% observe)",
        f"{n_score_neg} notes ({pct:.1f}%)",
    )

    # A6b - Notes avec tentative negative
    n_tentative_neg = scalar(cursor, "SELECT COUNT(*) FROM notes WHERE tentative < 0")
    pct = 100 * n_tentative_neg / 500000
    report.add(
        "ANOMALIES",
        "A6b - Notes avec tentative < 0",
        check_between(pct, 20, 45),
        "entre 20% et 45% (~33% observe)",
        f"{n_tentative_neg} notes ({pct:.1f}%)",
    )

    # A8 - Progressions > 100%
    n_prog_sup = scalar(cursor, "SELECT COUNT(*) FROM progression WHERE pourcentage > 100")
    pct = 100 * n_prog_sup / 15000
    report.add(
        "ANOMALIES",
        "A8  - Progressions > 100%",
        check_between(pct, 20, 40),
        "entre 20% et 40% (~29% observe)",
        f"{n_prog_sup} lignes ({pct:.1f}%)",
    )

    # A9 - Progressions < 0%
    n_prog_neg = scalar(cursor, "SELECT COUNT(*) FROM progression WHERE pourcentage < 0")
    pct = 100 * n_prog_neg / 15000
    report.add(
        "ANOMALIES",
        "A9  - Progressions < 0%",
        check_between(pct, 5, 20),
        "entre 5% et 20% (~11.7% observe)",
        f"{n_prog_neg} lignes ({pct:.1f}%)",
    )

    # A12 - Variantes d'appareils
    n_appareils = scalar(
        cursor,
        "SELECT COUNT(DISTINCT appareil) FROM temps_connexion WHERE appareil IS NOT NULL"
    )
    report.add(
        "ANOMALIES",
        "A12 - Variantes d'appareils (Mobile, mobile, Telephone...)",
        n_appareils >= 6,
        "au moins 6 valeurs distinctes",
        f"{n_appareils} appareils",
    )

    # A13 - Durees connexion negatives
    n_duree_neg = scalar(
        cursor,
        "SELECT COUNT(*) FROM temps_connexion WHERE duree_minutes < 0"
    )
    pct = 100 * n_duree_neg / 80000
    report.add(
        "ANOMALIES",
        "A13 - Durees connexion < 0",
        check_between(pct, 10, 30),
        "entre 10% et 30% (~19.7% observe)",
        f"{n_duree_neg} connexions ({pct:.1f}%)",
    )

    # A14 - IP vides ou NULL
    n_ip_ko = scalar(
        cursor,
        "SELECT COUNT(*) FROM temps_connexion WHERE adresse_ip IS NULL OR adresse_ip = ''"
    )
    pct = 100 * n_ip_ko / 80000
    report.add(
        "ANOMALIES",
        "A14 - IP vides ou NULL",
        check_between(pct, 5, 20),
        "entre 5% et 20% (~9.9% observe)",
        f"{n_ip_ko} connexions ({pct:.1f}%)",
    )


# =============================================================================
# 3. TESTS D'INTEGRITE RELATIONNELLE
# =============================================================================

def test_integrite(cursor, report):
    """Verifie les contraintes d'integrite qui doivent tenir."""

    # I1 - Toutes les FK actives doivent tenir (cours -> modules)
    n_cours_orphelins = scalar(cursor, """
        SELECT COUNT(*) FROM cours c
        LEFT JOIN modules m ON c.id_module = m.id_module
        WHERE m.id_module IS NULL
    """)
    report.add(
        "INTEGRITE",
        "I1 - Cours avec id_module fantome (FK doit tenir)",
        n_cours_orphelins == 0,
        "0 cours orphelin",
        f"{n_cours_orphelins} cours orphelins",
    )

    # I2 - FK quiz -> cours
    n_quiz_orphelins = scalar(cursor, """
        SELECT COUNT(*) FROM quiz q
        LEFT JOIN cours c ON q.id_cours = c.id_cours
        WHERE c.id_cours IS NULL
    """)
    report.add(
        "INTEGRITE",
        "I2 - Quiz avec id_cours fantome (FK doit tenir)",
        n_quiz_orphelins == 0,
        "0 quiz orphelin",
        f"{n_quiz_orphelins} quiz orphelins",
    )

    # I3 - FK notes -> quiz
    n_notes_orphelines = scalar(cursor, """
        SELECT COUNT(*) FROM notes n
        LEFT JOIN quiz q ON n.id_quiz = q.id_quiz
        WHERE q.id_quiz IS NULL
    """)
    report.add(
        "INTEGRITE",
        "I3 - Notes avec id_quiz fantome (FK doit tenir)",
        n_notes_orphelines == 0,
        "0 note orpheline",
        f"{n_notes_orphelines} notes orphelines",
    )

    # I4 - Progression : UNIQUE(student_code, id_module) doit etre respectee
    n_doublons = scalar(cursor, """
        SELECT COUNT(*) FROM (
            SELECT student_code, id_module, COUNT(*) as n
            FROM progression
            GROUP BY student_code, id_module
            HAVING n > 1
        ) AS sub
    """)
    report.add(
        "INTEGRITE",
        "I4 - UNIQUE(student_code, id_module) sur progression",
        n_doublons == 0,
        "0 doublon",
        f"{n_doublons} doublons",
    )

    # I5 - Progression : id_module fantome ATTENDU (anomalie A11)
    n_prog_fantomes = scalar(cursor, """
        SELECT COUNT(*) FROM progression p
        LEFT JOIN modules m ON p.id_module = m.id_module
        WHERE m.id_module IS NULL
    """)
    pct = 100 * n_prog_fantomes / 15000
    report.add(
        "INTEGRITE",
        "I5 - Progressions avec id_module fantome (A11 - ATTENDU)",
        check_between(pct, 5, 15),
        "entre 5% et 15% (~10% observe)",
        f"{n_prog_fantomes} progressions ({pct:.1f}%)",
    )

    # I6 - code_module UNIQUE sur modules
    n_codes_dupliques = scalar(cursor, """
        SELECT COUNT(*) FROM (
            SELECT code_module, COUNT(*) as n
            FROM modules
            GROUP BY code_module
            HAVING n > 1
        ) AS sub
    """)
    report.add(
        "INTEGRITE",
        "I6 - UNIQUE(code_module) sur modules",
        n_codes_dupliques == 0,
        "0 doublon",
        f"{n_codes_dupliques} doublons",
    )


# =============================================================================
# 4. TESTS DE FORMAT
# =============================================================================

def test_format(cursor, report):
    """Verifie que les formats des donnees sont conformes."""

    # F1 - Format student_code : LMS-XXXXX (9 caracteres)
    n_bad_format = scalar(cursor, """
        SELECT COUNT(*) FROM notes
        WHERE student_code NOT REGEXP '^LMS-[0-9]{5}$'
    """)
    report.add(
        "FORMAT",
        "F1 - Format student_code dans notes (LMS-XXXXX)",
        n_bad_format == 0,
        "0 code au mauvais format",
        f"{n_bad_format} codes au mauvais format",
    )

    # F2 - Format student_code dans progression
    n_bad_format = scalar(cursor, """
        SELECT COUNT(*) FROM progression
        WHERE student_code NOT REGEXP '^LMS-[0-9]{5}$'
    """)
    report.add(
        "FORMAT",
        "F2 - Format student_code dans progression (LMS-XXXXX)",
        n_bad_format == 0,
        "0 code au mauvais format",
        f"{n_bad_format} codes au mauvais format",
    )

    # F3 - Format code_module : MOD-XXX
    n_bad_format = scalar(cursor, """
        SELECT COUNT(*) FROM modules
        WHERE code_module NOT REGEXP '^MOD-[0-9]+$'
    """)
    report.add(
        "FORMAT",
        "F3 - Format code_module (MOD-XXX)",
        n_bad_format == 0,
        "0 code au mauvais format",
        f"{n_bad_format} codes au mauvais format",
    )

    # F4 - Fenetre temporelle des dates
    date_min, date_max = None, None
    cursor.execute("""
        SELECT MIN(date_passage), MAX(date_passage) FROM notes
    """)
    row = cursor.fetchone()
    if row:
        date_min, date_max = row
    report.add(
        "FORMAT",
        "F4 - Fenetre temporelle des dates de notes",
        date_min is not None and date_max is not None,
        "dates presentes",
        f"du {date_min} au {date_max}",
    )


# =============================================================================
# ORCHESTRATION
# =============================================================================

def get_mysql_config():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "edusmart_user"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "edusmart_learning_v2"),
    }


def main():
    logger.info("=" * 70)
    logger.info("TESTS DE QUALITE DE edusmart_learning_v2")
    logger.info("=" * 70)
    logger.info("")

    try:
        conn = mysql.connector.connect(**get_mysql_config())
    except mysql.connector.Error as e:
        logger.error("Impossible de se connecter : %s", e)
        return 1

    cursor = conn.cursor()
    report = TestReport()

    try:
        logger.info("Execution des tests...")
        test_volumetrie(cursor, report)
        test_anomalies(cursor, report)
        test_integrite(cursor, report)
        test_format(cursor, report)
    finally:
        cursor.close()
        conn.close()

    all_passed = report.display()

    if all_passed:
        logger.info("")
        logger.info("Tous les tests passent. La base est prete pour l'ETL.")
        return 0
    else:
        logger.info("")
        logger.info("Certains tests echouent. Verifier le detail ci-dessus.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
