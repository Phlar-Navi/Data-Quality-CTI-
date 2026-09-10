-- Script de création de la table CDR_EVENTS pour les données CTI
-- Basé sur la structure : EVENT_TIME;TS;CONNID;ANI;DNIS;...

-- Se connecter : python test_utils\run_sql.py create_table.sql

-- Supprimer la table si elle existe
DROP TABLE CDR_EVENTS CASCADE CONSTRAINTS;

-- Créer la table principale
CREATE TABLE CDR_EVENTS (
    -- Colonnes temporelles (clés pour monitoring)
    EVENT_TIME VARCHAR2(50),           -- Format: 2026-06-19_01:00:53
    EVENT_DATE DATE,                    -- Date de l'événement
    FILE_DATE DATE,                     -- Date du fichier
    TS NUMBER(15),                      -- Timestamp Unix
    
    -- Identifiants
    CONNID VARCHAR2(50) PRIMARY KEY,    -- Identifiant unique de connexion
    ANI VARCHAR2(20),                   -- Calling number
    DNIS VARCHAR2(20),                  -- Called number (8900)
    
    -- File d'attente et routage
    LAST_VQ VARCHAR2(100),              -- Dernière VQ (Virtual Queue)
    PLACE_KEY NUMBER(10),               -- -2 si pas de place
    UD_SITE_CHOISI VARCHAR2(50),        -- Site choisi
    UD_SITE_CIBLE VARCHAR2(50),         -- Site cible
    
    -- Résultats techniques
    TECHNICAL_RESULT VARCHAR2(50),      -- CustomerAbandoned, Completed, etc.
    TECHNICAL_RESULT_CODE VARCHAR2(50), -- CUSTOMERABANDONED, COMPLETED, etc.
    RESULT_REASON VARCHAR2(100),        -- AbandonedWhileQueued, Unspecified, etc.
    RESULT_REASON_CODE VARCHAR2(100),   -- ABANDONEDWHILEQUEUED, UNSPECIFIED, etc.
    
    -- Type d'interaction
    INTERACTION_TYPE VARCHAR2(50),      -- Inbound
    INTERACTION_TYPE_CODE VARCHAR2(50), -- INBOUND
    
    -- Agent et ressource
    PLACE VARCHAR2(50),                 -- NO_VALUE ou numéro
    RESOURCE_TYPE VARCHAR2(50),         -- RoutingPoint, Agent
    RESOURCE_NAME VARCHAR2(50),         -- Nom de la ressource (ex: YSXL1934)
    NOM VARCHAR2(100),                  -- Nom complet de l'agent
    
    -- Durées (en secondes)
    DUREE_CONVERSATION NUMBER(10),      -- Durée de conversation
    DUREE_FILE NUMBER(10),              -- Durée d'attente en file
    
    -- Segmentation
    TECHNICAL_DESCRIPTOR_KEY NUMBER(10),
    SEGMENT VARCHAR2(100),              -- MED_FRE_OM_PCCI, etc.
    
    -- Métadonnées fichier source
    ORIGINAL_FILE_NAME VARCHAR2(200),
    ORIGINAL_FILE_DATE DATE,
    ORIGINAL_FILE_SIZE NUMBER(15),
    ORIGINAL_FILE_LINE_COUNT NUMBER(10),
    INSERT_DATE TIMESTAMP,
    
    -- Métadonnées d'import
    LOADED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Créer des index pour les requêtes de monitoring
CREATE INDEX IDX_EVENT_DATE ON CDR_EVENTS(EVENT_DATE);
CREATE INDEX IDX_FILE_DATE ON CDR_EVENTS(FILE_DATE);
CREATE INDEX IDX_TECHNICAL_RESULT ON CDR_EVENTS(TECHNICAL_RESULT);
CREATE INDEX IDX_SEGMENT ON CDR_EVENTS(SEGMENT);
CREATE INDEX IDX_SITE_CIBLE ON CDR_EVENTS(UD_SITE_CIBLE);

-- Extraire l'heure de EVENT_TIME pour distribution horaire
ALTER TABLE CDR_EVENTS ADD EVENT_HOUR NUMBER(2) 
    GENERATED ALWAYS AS (
        TO_NUMBER(SUBSTR(EVENT_TIME, 12, 2))
    ) VIRTUAL;

CREATE INDEX IDX_EVENT_HOUR ON CDR_EVENTS(EVENT_HOUR);

-- Accorder les droits à monitoring_user
GRANT SELECT ON CDR_EVENTS TO monitoring_user;

-- Vérifier la structure
DESC CDR_EVENTS;

-- Afficher un résumé
SELECT 'Table CDR_EVENTS creee avec succes' as STATUS FROM DUAL;
