-- ================================================================
-- SILVER: Saude (SIH-SUS internacoes)
-- ================================================================
CREATE OR REPLACE TEMP VIEW silver_saude AS
SELECT
    CAST(cod_ibge_municipio AS INT)    AS cod_ibge,
    municipio,
    uf,
    TO_DATE(CONCAT(mes_ano, '-01'),'yyyy-MM-dd') AS data_ref,
    mes_ano,
    YEAR(TO_DATE(CONCAT(mes_ano,'-01'),'yyyy-MM-dd'))  AS ano,
    MONTH(TO_DATE(CONCAT(mes_ano,'-01'),'yyyy-MM-dd')) AS mes,
    cid10,
    CASE
        WHEN cid10 LIKE 'A0%' THEN 'Gastroenterites'
        WHEN cid10 = 'B15'    THEN 'Hepatite A'
        ELSE 'Outros'
    END                                AS grupo_cid,
    CAST(n_internacoes AS INT)         AS n_internacoes,
    CAST(obitos AS INT)                AS obitos,
    CAST(dias_permanencia_media AS DOUBLE) AS dias_permanencia_media,
    'sih_sus'                          AS fonte_bronze,
    current_timestamp()                AS data_ingestao
FROM bronze_sih;
