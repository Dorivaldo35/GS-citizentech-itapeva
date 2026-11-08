-- ================================================================
-- ANALYTICS: respostas as perguntas do enunciado (item 6 da GS)
-- ================================================================
-- Rode apos o pipeline Gold estar materializado.

-- -----------------------------------------------------------------
-- P1. Linha do tempo: quando os parametros comecaram a se desviar?
-- -----------------------------------------------------------------
SELECT ano, mes, eta,
       ROUND(AVG(turbidez_ntu), 2)       AS turbidez_media,
       ROUND(AVG(cloro_residual_mg_l),2) AS cloro_medio,
       SUM(flag_nao_conforme)            AS n_nao_conformes
FROM silver_qualidade_agua
WHERE data_coleta >= DATE '2026-06-01'
GROUP BY ano, mes, eta
ORDER BY ano, mes, eta;

-- -----------------------------------------------------------------
-- P2. Correlacao espacial: qual ETA concentra mais internacoes?
-- -----------------------------------------------------------------
SELECT * FROM gold_ranking_eta;

-- -----------------------------------------------------------------
-- P3. Fator climatico: dias com chuva>40mm precederam picos?
-- -----------------------------------------------------------------
WITH picos AS (
    SELECT data, SUM(internacoes) AS internacoes_dia
    FROM gold_fato_crise
    GROUP BY data
),
chuvas_fortes AS (
    SELECT data, precipitacao_mm
    FROM silver_clima
    WHERE precipitacao_mm > 40
)
SELECT cf.data            AS data_chuva_forte,
       cf.precipitacao_mm AS mm_chuva,
       p.data             AS data_pico,
       p.internacoes_dia
FROM chuvas_fortes cf
LEFT JOIN picos p
  ON p.data BETWEEN DATE_ADD(cf.data, 1) AND DATE_ADD(cf.data, 10)
ORDER BY cf.data;

-- -----------------------------------------------------------------
-- P4. Historico de alertas: SISAGUA ja sinalizava nos ultimos anos?
-- -----------------------------------------------------------------
SELECT ano,
       SUM(flag_nao_conforme) AS nao_conformes,
       COUNT(*)               AS total_coletas,
       ROUND(100.0 * SUM(flag_nao_conforme) / COUNT(*), 1) AS pct_nao_conforme
FROM silver_qualidade_agua
GROUP BY ano
ORDER BY ano;

-- -----------------------------------------------------------------
-- P5. Cobertura da resposta: pontos de pipa estao nos piores bairros?
-- -----------------------------------------------------------------
WITH risco AS (
    SELECT bairro, nivel_risco, taxa_internacao_100k
    FROM gold_indicador_risco_bairro
),
pontos AS (
    SELECT bairro,
           COUNT(*) AS n_pontos,
           SUM(CAST(litros_dia_estimado AS INT)) AS litros_total_dia
    FROM bronze_pontos
    GROUP BY bairro
)
SELECT r.bairro,
       r.nivel_risco,
       r.taxa_internacao_100k,
       COALESCE(p.n_pontos, 0)        AS n_pontos_distribuicao,
       COALESCE(p.litros_total_dia,0) AS litros_dia
FROM risco r
LEFT JOIN pontos p ON r.bairro = p.bairro
ORDER BY r.taxa_internacao_100k DESC;

-- -----------------------------------------------------------------
-- P6. Impacto educacional (quando os bairros com escola fecham)
-- -----------------------------------------------------------------
-- Usa `endereco_referencia` do Bronze crise_2026
SELECT bairro,
       endereco_referencia  AS escola,
       CAST(data_inicio AS DATE) AS data_inicio_distribuicao,
       veiculos_dia,
       litros_dia_estimado
FROM bronze_pontos
ORDER BY bairro;

-- -----------------------------------------------------------------
-- P7. Serie historica estruturada: SNIS -> contexto da infra
-- -----------------------------------------------------------------
SELECT ano,
       ROUND(cobertura_agua_pct, 1)            AS cob_agua_pct,
       ROUND(cobertura_esgoto_pct, 1)          AS cob_esgoto_pct,
       ROUND(perdas_distribuicao_pct, 1)       AS perdas_pct,
       ROUND(indice_tratamento_esgoto_pct, 1)  AS trat_esgoto_pct
FROM bronze_snis
ORDER BY ano;
