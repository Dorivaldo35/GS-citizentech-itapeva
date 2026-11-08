-- ================================================================
-- SILVER: Clima (INMET A714) + features de precipitacao acumulada
-- ================================================================
CREATE OR REPLACE TEMP VIEW silver_clima AS
SELECT
    estacao,
    municipio,
    uf,
    CAST(data AS DATE) AS data,
    CAST(precipitacao_mm AS DOUBLE) AS precipitacao_mm,
    CAST(temperatura_c AS DOUBLE)   AS temperatura_c,
    CAST(umidade_pct AS DOUBLE)     AS umidade_pct,
    'inmet' AS fonte_bronze
FROM bronze_inmet;

-- Window features: chuva acumulada 7 e 14 dias (Feature Engineering)
CREATE OR REPLACE TEMP VIEW silver_clima_feat AS
SELECT
    *,
    SUM(precipitacao_mm) OVER (
        ORDER BY data ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS chuva_acum_7d,
    SUM(precipitacao_mm) OVER (
        ORDER BY data ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
    ) AS chuva_acum_14d
FROM silver_clima;
