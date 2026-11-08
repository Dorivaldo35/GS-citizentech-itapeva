-- ================================================================
-- SILVER: Qualidade da agua (padronizacao do SISAGUA)
-- ================================================================
-- Executar apos registrar a view `bronze_sisagua` (CSV bronze).
-- Objetivo: tipar colunas, derivar flag de nao-conformidade e deixar
-- o dataset pronto para joins com saude e clima.

CREATE OR REPLACE TEMP VIEW silver_qualidade_agua AS
SELECT
    CAST(cod_ibge AS INT)                     AS cod_ibge,
    municipio,
    uf,
    eta,
    CAST(data_coleta AS DATE)                 AS data_coleta,
    YEAR(CAST(data_coleta AS DATE))           AS ano,
    MONTH(CAST(data_coleta AS DATE))          AS mes,
    CAST(cloro_residual_mg_l AS DOUBLE)       AS cloro_residual_mg_l,
    CAST(turbidez_ntu AS DOUBLE)              AS turbidez_ntu,
    CAST(coliformes_totais_ufc AS INT)        AS coliformes_totais_ufc,
    CAST(ecoli_ufc AS INT)                    AS ecoli_ufc,
    conformidade,
    -- Regras do Ministerio da Saude (Portaria GM/MS 888/2021)
    CASE
        WHEN cloro_residual_mg_l < 0.2 THEN 1
        WHEN turbidez_ntu > 5          THEN 1
        WHEN ecoli_ufc > 0             THEN 1
        ELSE 0
    END                                       AS flag_nao_conforme,
    CASE
        WHEN ecoli_ufc > 0 THEN 'contaminacao_microbiologica'
        WHEN turbidez_ntu > 5 THEN 'turbidez_elevada'
        WHEN cloro_residual_mg_l < 0.2 THEN 'cloro_insuficiente'
        ELSE 'ok'
    END                                       AS motivo_nao_conforme,
    'sisagua'                                 AS fonte_bronze,
    current_timestamp()                        AS data_ingestao
FROM bronze_sisagua;
