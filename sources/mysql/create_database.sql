-- =============================================================================
--  create_database.sql
--  EduSmart Decision Platform - Source 2 (MySQL) - v2 (equipe MySQL)
-- =============================================================================
--
--  Description
--  -----------
--  Cree la base edusmart_learning_v2 avec les 6 tables du modele pedagogique.
--  La base est ensuite peuplee par insert_data.py qui charge les CSV
--  partages sur le Drive.
--
--  Ce fichier est idempotent : le rejouer produit toujours le meme resultat.
--
--  Utilisation
--  -----------
--     mysql -u root -p < create_database.sql
--
--  Choix techniques structurants
--  -----------------------------
--  - UUID stockes en CHAR(36) pour la lisibilite au debogage
--  - Encodage utf8mb4 avec collation utf8mb4_unicode_ci (Unicode complet)
--  - Moteur InnoDB (transactions ACID + FK)
--  - Contrainte UNIQUE(student_code, id_module) sur progression
--    (materialise le snapshot metier : une progression par etudiant/module)
--  - Absence VOLONTAIRE de FK sur student_code
--    (identifiant externe partage avec les autres sources)
--  - Absence VOLONTAIRE de FK sur progression.id_module
--    (les CSV contiennent ~10% de id_module fantomes pour l'ETL)
--  - Absence VOLONTAIRE de FK sur progression.dernier_cours
--    (les CSV contiennent ~69% de dernier_cours fantomes pour l'ETL)
--  - Certaines CHECK volontairement omises pour permettre les anomalies
--    pedagogiques (voir docs/anomalies.md)
--
-- =============================================================================

-- Creation de la base
CREATE DATABASE IF NOT EXISTS edusmart_learning_v2
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE edusmart_learning_v2;

-- =============================================================================
-- SUPPRESSION IDEMPOTENTE DES TABLES (dans l'ordre inverse des dependances)
-- =============================================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS temps_connexion;
DROP TABLE IF EXISTS progression;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS quiz;
DROP TABLE IF EXISTS cours;
DROP TABLE IF EXISTS modules;

SET FOREIGN_KEY_CHECKS = 1;


-- =============================================================================
-- 1. TABLE modules
-- =============================================================================
--  Bloc Catalogue : grandes unites d'enseignement
--  Volume attendu : 500 lignes
--  CHECK conservees : duree_heures > 0
-- =============================================================================

CREATE TABLE modules (
    id_module     CHAR(36)     NOT NULL,
    code_module   VARCHAR(20)  NOT NULL,
    nom_module    VARCHAR(255) NOT NULL,
    categorie     VARCHAR(100) NOT NULL,
    niveau        VARCHAR(30)  NOT NULL,
    duree_heures  INTEGER      NOT NULL,
    actif         BOOLEAN      NOT NULL DEFAULT TRUE,

    PRIMARY KEY (id_module),
    UNIQUE KEY uk_modules_code (code_module),
    CHECK (duree_heures > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT = 'Catalogue des modules pedagogiques';


-- =============================================================================
-- 2. TABLE cours
-- =============================================================================
--  Bloc Catalogue : contenus pedagogiques par module
--  Volume attendu : 2 000 lignes
--  FK cours.id_module -> modules.id_module (integrite garantie par les CSV)
-- =============================================================================

CREATE TABLE cours (
    id_cours       CHAR(36)     NOT NULL,
    id_module      CHAR(36)     NOT NULL,
    titre          VARCHAR(255) NOT NULL,
    ordre          INTEGER      NOT NULL,
    duree_minutes  INTEGER      NOT NULL,
    type_cours     VARCHAR(30)  NOT NULL,
    statut         VARCHAR(20)  NOT NULL DEFAULT 'PUBLIE',

    PRIMARY KEY (id_cours),
    CONSTRAINT fk_cours_module
        FOREIGN KEY (id_module) REFERENCES modules(id_module)
        ON DELETE RESTRICT ON UPDATE RESTRICT
    -- CHECK ordre > 0 volontairement omise (l'ordre peut etre 0 dans les CSV)
    -- CHECK duree_minutes > 0 volontairement omise (anomalie)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT = 'Cours composant les modules';

CREATE INDEX idx_cours_module ON cours(id_module);


-- =============================================================================
-- 3. TABLE quiz
-- =============================================================================
--  Bloc Catalogue : evaluations liees aux cours
--  Volume attendu : 5 000 lignes
--  FK quiz.id_cours -> cours.id_cours (integrite garantie par les CSV)
--  CHECK duree_minutes volontairement omise (anomalies duree quiz)
-- =============================================================================

CREATE TABLE quiz (
    id_quiz        CHAR(36)      NOT NULL,
    id_cours       CHAR(36)      NOT NULL,
    titre          VARCHAR(255)  NOT NULL,
    nb_questions   INTEGER       NOT NULL,
    score_max      NUMERIC(5,2)  NOT NULL,
    duree_minutes  INTEGER       NOT NULL,

    PRIMARY KEY (id_quiz),
    CONSTRAINT fk_quiz_cours
        FOREIGN KEY (id_cours) REFERENCES cours(id_cours)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CHECK (nb_questions > 0),
    CHECK (score_max > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT = 'Quiz associes aux cours';

CREATE INDEX idx_quiz_cours ON quiz(id_cours);


-- =============================================================================
-- 4. TABLE notes
-- =============================================================================
--  Bloc Activite : tentatives de quiz par les etudiants (evenementielle)
--  Volume attendu : 500 000 lignes
--  FK notes.id_quiz -> quiz.id_quiz (integrite garantie par les CSV)
--  CHECK score >= 0 omise volontairement (anomalie : scores negatifs)
--  CHECK tentative >= 1 omise volontairement (anomalie : tentatives negatives)
-- =============================================================================

CREATE TABLE notes (
    id_note       CHAR(36)      NOT NULL,
    id_quiz       CHAR(36)      NOT NULL,
    student_code  VARCHAR(30)   NOT NULL,
    date_passage  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    score         NUMERIC(6,2)  NOT NULL,
    tentative     INTEGER       NOT NULL DEFAULT 1,
    valide        BOOLEAN       NOT NULL DEFAULT FALSE,

    PRIMARY KEY (id_note),
    CONSTRAINT fk_notes_quiz
        FOREIGN KEY (id_quiz) REFERENCES quiz(id_quiz)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT = 'Historique des tentatives de quiz';

CREATE INDEX idx_notes_quiz ON notes(id_quiz);
CREATE INDEX idx_notes_student ON notes(student_code);
CREATE INDEX idx_notes_date ON notes(date_passage);


-- =============================================================================
-- 5. TABLE progression
-- =============================================================================
--  Bloc Activite : suivi de l'avancement des etudiants (snapshot metier)
--  Volume attendu : 15 000 lignes (1 par etudiant dans cette version)
--
--  IMPORTANT : UNIQUE(student_code, id_module) est ACTIVE.
--  Elle est respectee par les CSV existants (verifie : 0 doublons).
--  Cette contrainte materialise la nature snapshot de la table.
--
--  IMPORTANT : PAS DE FK vers modules.
--  Les CSV contiennent ~10% de progressions avec id_module fantome (anomalie
--  volontaire A11 pour l'ETL). Une FK RESTRICT bloquerait le chargement.
--
--  IMPORTANT : PAS DE FK vers cours pour dernier_cours.
--  Les CSV contiennent ~69% de dernier_cours fantomes (anomalie A10 forte).
-- =============================================================================

CREATE TABLE progression (
    id_progression  CHAR(36)      NOT NULL,
    student_code    VARCHAR(30)   NOT NULL,
    id_module       CHAR(36)      NOT NULL,
    pourcentage     NUMERIC(6,2)  NOT NULL,
    dernier_cours   CHAR(36)      NULL,
    date_maj        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id_progression),
    UNIQUE KEY uk_progression_student_module (student_code, id_module)
    -- Aucune FK volontairement (voir commentaire ci-dessus)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT = 'Snapshot de progression par etudiant et par module';

CREATE INDEX idx_progression_student ON progression(student_code);
CREATE INDEX idx_progression_module ON progression(id_module);


-- =============================================================================
-- 6. TABLE temps_connexion
-- =============================================================================
--  Bloc Activite : historique des sessions de connexion (evenementielle)
--  Volume attendu : 80 000 lignes
--  Table independante (student_code = identifiant externe partage)
--  Aucune CHECK sur duree_minutes (anomalie : durees negatives)
-- =============================================================================

CREATE TABLE temps_connexion (
    id_connexion      CHAR(36)     NOT NULL,
    student_code      VARCHAR(30)  NOT NULL,
    date_connexion    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_deconnexion  TIMESTAMP    NULL,
    duree_minutes     INTEGER      NULL,
    appareil          VARCHAR(50)  NULL,
    navigateur        VARCHAR(50)  NULL,
    adresse_ip        VARCHAR(45)  NULL,

    PRIMARY KEY (id_connexion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT = 'Historique des sessions de connexion';

CREATE INDEX idx_connexion_student ON temps_connexion(student_code);
CREATE INDEX idx_connexion_date ON temps_connexion(date_connexion);


-- =============================================================================
-- VERIFICATION FINALE : les 6 tables sont creees
-- =============================================================================
SHOW TABLES;


-- =============================================================================
-- PREPARATION DE L'UTILISATEUR APPLICATIF (a executer UNE SEULE FOIS, en root)
-- =============================================================================
-- Decommenter les lignes ci-dessous lors de la premiere execution.
-- Adapter le mot de passe (a mettre dans .env).
--
-- CREATE USER IF NOT EXISTS 'edusmart_user'@'localhost' IDENTIFIED BY 'change_me_in_env';
-- GRANT ALL PRIVILEGES ON edusmart_learning_v2.* TO 'edusmart_user'@'localhost';
-- FLUSH PRIVILEGES;
-- =============================================================================
