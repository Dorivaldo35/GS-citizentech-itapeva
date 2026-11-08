-- ================================================================
-- GOLD: Indicadores estrategicos para a CitizenTech
-- ================================================================

-- 4.1 Fato diario da crise 2026 (bairro x dia)
CREATE OR REPLACE TEMP VIEW gold_fato_crise AS
WITH casos AS (
    SELECT CAST(data AS DATE) AS data,
           bairro, eta,
           CAST(casos_notificados AS INT) AS casos_notificados,
           CAST(internacoes AS INT)       AS internacoes
    FROM bronze_casos
)
SELECT
    c.data,
    c.bairro,
    c.eta,
    b.populacao,
    b.classe_renda,
    b.dom_rede_agua_pct,
    c.casos_notificados,
    c.internacoes,
    ROUND(c.internacoes * 100000.0 / b.populacao, 2) AS taxa_internacao_100k,
    cf.precipitacao_mm,
    cf.chuva_acum_7d,
    cf.chuva_acum_14d
FROM casos c
JOIN silver_bairros_dim b ON c.bairro = b.bairro
LEFT JOIN silver_clima_feat cf ON c.data = cf.data;


-- 4.2 Indicador de risco agregado por bairro (desde inicio do surto)
CREATE OR REPLACE TEMP VIEW gold_indicador_risco_bairro AS
WITH agg AS (
    SELECT
        bairro, eta, classe_renda, MAX(populacao) AS populacao,
        SUM(casos_notificados) AS total_casos,
        SUM(internacoes)       AS total_internacoes
    FROM gold_fato_crise
    WHERE data >= DATE '2026-10-20'
    GROUP BY bairro, eta, classe_renda
)
SELECT
    bairro, eta, classe_renda, populacao,
    total_casos, total_internacoes,
    ROUND(total_internacoes * 100000.0 / populacao, 2) AS taxa_internacao_100k,
    CASE
        WHEN total_internacoes * 100000.0 / populacao > 150 THEN 'CRITICO'
        WHEN total_internacoes * 100000.0 / populacao > 80  THEN 'ALTO'
        WHEN total_internacoes * 100000.0 / populacao > 30  THEN 'MEDIO'
        ELSE 'BAIXO'
    END AS nivel_risco
FROM agg
ORDER BY taxa_internacao_100k DESC;


-- 4.3 Ranking entre as ETAs (Pilao vs Aranhas)
CREATE OR REPLACE TEMP VIEW gold_ranking_eta AS
SELECT
    eta,
    SUM(casos_notificados)   AS casos_total,
    SUM(internacoes)         AS internacoes_total,
    SUM(populacao)           AS pop_total,
    ROUND(SUM(internacoes) * 100000.0 / SUM(populacao), 2) AS taxa_int_100k
FROM gold_fato_crise
WHERE data >= DATE '2026-10-20'
GROUP BY eta
ORDER BY taxa_int_100k DESC;


-- 4.4 Linha do tempo semanal (casos + chuva)
CREATE OR REPLACE TEMP VIEW gold_linha_tempo_crise AS
WITH sem_casos AS (
    SELECT DATE_TRUNC('WEEK', data) AS semana,
           SUM(casos_notificados)  AS casos,
           SUM(internacoes)         AS internacoes
    FROM gold_fato_crise
    GROUP BY DATE_TRUNC('WEEK', data)
),
sem_chuva AS (
    SELECT DATE_TRUNC('WEEK', data) AS semana,
           SUM(precipitacao_mm) AS chuva_semanal
    FROM silver_clima
    WHERE data >= DATE '2026-09-01'
    GROUP BY DATE_TRUNC('WEEK', data)
)
SELECT c.semana, c.casos, c.internacoes, ch.chuva_semanal
FROM sem_casos c
LEFT JOIN sem_chuva ch ON c.semana = ch.semana
ORDER BY c.semana;
