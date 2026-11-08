"""
Pipeline LOCAL (Pandas + DuckDB) - mesmo pipeline do notebook Databricks mas
sem depender de Java/Spark. Util para validacao rapida no notebook do aluno.

Execucao:
    python notebooks/pipeline_local.py

Databricks: use notebooks/pipeline_itapeva.py (PySpark).
"""
from __future__ import annotations
from pathlib import Path

import duckdb
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BRONZE = ROOT / "data" / "bronze"
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold"
SILVER.mkdir(parents=True, exist_ok=True)
GOLD.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(database=":memory:")


def read_bronze_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} nao existe. Rode primeiro: "
            "python -m src.utils.gera_dados_sinteticos"
        )
    return pd.read_csv(path)


print("=" * 70)
print("1. BRONZE -> leitura")
print("=" * 70)

bronze = {
    "bronze_sisagua": read_bronze_csv(BRONZE / "sisagua" / "sisagua_itapeva_2015_2026.csv"),
    "bronze_sih":     read_bronze_csv(BRONZE / "sih_sus" / "sih_itapeva_2018_2026.csv"),
    "bronze_inmet":   read_bronze_csv(BRONZE / "inmet"   / "inmet_a714_2020_2026.csv"),
    "bronze_snis":    read_bronze_csv(BRONZE / "snis"    / "snis_itapeva.csv"),
    "bronze_bairros": read_bronze_csv(BRONZE / "ibge"    / "bairros_itapeva.csv"),
    "bronze_casos":   read_bronze_csv(BRONZE / "crise_2026" / "casos_por_bairro_diario.csv"),
    "bronze_pontos":  read_bronze_csv(BRONZE / "crise_2026" / "pontos_distribuicao.csv"),
    "bronze_laudos":  read_bronze_csv(BRONZE / "crise_2026" / "laudos_ial.csv"),
}
for nome, df in bronze.items():
    con.register(nome, df)
    print(f"  {nome:>18}: {len(df):>7} linhas")


print("\n" + "=" * 70)
print("2. SILVER -> padronizacao via SQL")
print("=" * 70)

con.execute("""
CREATE OR REPLACE TABLE silver_qualidade_agua AS
SELECT
    CAST(cod_ibge AS INTEGER)              AS cod_ibge,
    municipio, uf, eta,
    CAST(data_coleta AS DATE)              AS data_coleta,
    EXTRACT(year  FROM CAST(data_coleta AS DATE)) AS ano,
    EXTRACT(month FROM CAST(data_coleta AS DATE)) AS mes,
    CAST(cloro_residual_mg_l AS DOUBLE)    AS cloro_residual_mg_l,
    CAST(turbidez_ntu AS DOUBLE)           AS turbidez_ntu,
    CAST(coliformes_totais_ufc AS INTEGER) AS coliformes_totais_ufc,
    CAST(ecoli_ufc AS INTEGER)             AS ecoli_ufc,
    conformidade,
    CASE
        WHEN cloro_residual_mg_l < 0.2 THEN 1
        WHEN turbidez_ntu > 5          THEN 1
        WHEN ecoli_ufc > 0             THEN 1
        ELSE 0
    END AS flag_nao_conforme,
    'sisagua' AS fonte_bronze,
    current_timestamp AS data_ingestao
FROM bronze_sisagua
""")

con.execute("""
CREATE OR REPLACE TABLE silver_saude AS
SELECT
    CAST(cod_ibge_municipio AS INTEGER) AS cod_ibge,
    municipio, uf,
    CAST(mes_ano || '-01' AS DATE) AS data_ref,
    mes_ano,
    cid10,
    CASE
        WHEN cid10 LIKE 'A0%' THEN 'Gastroenterites'
        WHEN cid10 = 'B15'    THEN 'Hepatite A'
        ELSE 'Outros' END AS grupo_cid,
    CAST(n_internacoes AS INTEGER) AS n_internacoes,
    CAST(obitos AS INTEGER) AS obitos,
    CAST(dias_permanencia_media AS DOUBLE) AS dias_permanencia_media,
    'sih_sus' AS fonte_bronze
FROM bronze_sih
""")

con.execute("""
CREATE OR REPLACE TABLE silver_clima AS
SELECT
    estacao, municipio, uf,
    CAST(data AS DATE) AS data,
    CAST(precipitacao_mm AS DOUBLE) AS precipitacao_mm,
    CAST(temperatura_c AS DOUBLE)   AS temperatura_c,
    CAST(umidade_pct AS DOUBLE)     AS umidade_pct,
    'inmet' AS fonte_bronze
FROM bronze_inmet
""")

con.execute("""
CREATE OR REPLACE TABLE silver_clima_feat AS
SELECT
    *,
    SUM(precipitacao_mm) OVER (ORDER BY data ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
        AS chuva_acum_7d,
    SUM(precipitacao_mm) OVER (ORDER BY data ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
        AS chuva_acum_14d
FROM silver_clima
""")

con.execute("""
CREATE OR REPLACE TABLE silver_bairros_dim AS
SELECT
    CAST(cod_ibge AS INTEGER) AS cod_ibge,
    bairro, eta, classe_renda,
    CAST(populacao AS INTEGER) AS populacao,
    CAST(lat AS DOUBLE) AS lat,
    CAST(lon AS DOUBLE) AS lon,
    CAST(domicilios_rede_agua_pct AS DOUBLE) AS dom_rede_agua_pct
FROM bronze_bairros
""")

for t in ["silver_qualidade_agua", "silver_saude", "silver_clima",
          "silver_clima_feat", "silver_bairros_dim"]:
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:>24}: {n:>7} linhas")

# salva em parquet para o dashboard
con.execute(f"COPY silver_qualidade_agua TO '{SILVER/'qualidade_agua_mensal.parquet'}' (FORMAT PARQUET)")
con.execute(f"COPY silver_saude TO '{SILVER/'saude_mensal_itapeva.parquet'}' (FORMAT PARQUET)")
con.execute(f"COPY silver_clima TO '{SILVER/'clima_diario_itapeva.parquet'}' (FORMAT PARQUET)")
con.execute(f"COPY silver_bairros_dim TO '{SILVER/'bairros_itapeva_dim.parquet'}' (FORMAT PARQUET)")


print("\n" + "=" * 70)
print("3. GOLD -> indicadores")
print("=" * 70)

con.execute("""
CREATE OR REPLACE TABLE gold_fato_crise AS
WITH casos AS (
    SELECT CAST(data AS DATE) AS data,
           bairro, eta,
           CAST(casos_notificados AS INTEGER) AS casos_notificados,
           CAST(internacoes AS INTEGER)       AS internacoes
    FROM bronze_casos
)
SELECT
    c.data, c.bairro, c.eta,
    b.populacao, b.classe_renda, b.dom_rede_agua_pct,
    c.casos_notificados, c.internacoes,
    ROUND(c.internacoes * 100000.0 / b.populacao, 2) AS taxa_internacao_100k,
    cf.precipitacao_mm, cf.chuva_acum_7d, cf.chuva_acum_14d
FROM casos c
JOIN silver_bairros_dim b ON c.bairro = b.bairro
LEFT JOIN silver_clima_feat cf ON c.data = cf.data
""")

con.execute("""
CREATE OR REPLACE TABLE gold_indicador_risco_bairro AS
WITH agg AS (
    SELECT bairro, eta, classe_renda, MAX(populacao) AS populacao,
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
        ELSE 'BAIXO' END AS nivel_risco
FROM agg
ORDER BY taxa_internacao_100k DESC
""")

con.execute("""
CREATE OR REPLACE TABLE gold_ranking_eta AS
SELECT
    eta,
    SUM(casos_notificados) AS casos_total,
    SUM(internacoes)       AS internacoes_total,
    SUM(populacao)         AS pop_total,
    ROUND(SUM(internacoes) * 100000.0 / SUM(populacao), 2) AS taxa_int_100k
FROM gold_fato_crise
WHERE data >= DATE '2026-10-20'
GROUP BY eta
ORDER BY taxa_int_100k DESC
""")

con.execute("""
CREATE OR REPLACE TABLE gold_linha_tempo_crise AS
WITH sem_casos AS (
    SELECT DATE_TRUNC('week', data) AS semana,
           SUM(casos_notificados)  AS casos,
           SUM(internacoes)         AS internacoes
    FROM gold_fato_crise GROUP BY DATE_TRUNC('week', data)
),
sem_chuva AS (
    SELECT DATE_TRUNC('week', data) AS semana,
           SUM(precipitacao_mm) AS chuva_semanal
    FROM silver_clima
    WHERE data >= DATE '2026-09-01'
    GROUP BY DATE_TRUNC('week', data)
)
SELECT c.semana, c.casos, c.internacoes, ch.chuva_semanal
FROM sem_casos c
LEFT JOIN sem_chuva ch ON c.semana = ch.semana
ORDER BY c.semana
""")

con.execute(f"COPY gold_fato_crise TO '{GOLD/'fato_crise_2026_diario.parquet'}' (FORMAT PARQUET)")
con.execute(f"COPY gold_indicador_risco_bairro TO '{GOLD/'indicador_risco_bairro.parquet'}' (FORMAT PARQUET)")
con.execute(f"COPY gold_ranking_eta TO '{GOLD/'ranking_eta.parquet'}' (FORMAT PARQUET)")
con.execute(f"COPY gold_linha_tempo_crise TO '{GOLD/'linha_tempo_crise.parquet'}' (FORMAT PARQUET)")

for t in ["gold_fato_crise", "gold_indicador_risco_bairro",
          "gold_ranking_eta", "gold_linha_tempo_crise"]:
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:>30}: {n:>5} linhas")


print("\n" + "=" * 70)
print("4. ML -> clusterizacao + previsao de internacoes")
print("=" * 70)

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

risco = con.execute("SELECT * FROM gold_indicador_risco_bairro").df()
X = risco[["populacao", "total_casos", "taxa_internacao_100k"]].fillna(0)
X_s = StandardScaler().fit_transform(X)
km = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X_s)
risco["cluster"] = km.labels_
print("\nClusterizacao de bairros:")
print(risco[["bairro", "eta", "classe_renda", "nivel_risco", "cluster"]].to_string(index=False))

print("\nPrevisao de internacoes (RandomForest):")
fato = con.execute("SELECT * FROM gold_fato_crise").df().sort_values(["bairro", "data"])
fato["casos_lag1"] = fato.groupby("bairro")["casos_notificados"].shift(1).fillna(0)
fato["chuva_acum_7d"] = fato["chuva_acum_7d"].fillna(0)
feat = ["chuva_acum_7d", "casos_lag1", "populacao"]
X, y = fato[feat], fato["internacoes"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
rf = RandomForestRegressor(n_estimators=200, random_state=42).fit(Xtr, ytr)
yp = rf.predict(Xte)
print(f"  MAE: {mean_absolute_error(yte, yp):.3f}")
print(f"  R^2: {r2_score(yte, yp):.3f}")
for f, imp in zip(feat, rf.feature_importances_):
    print(f"    {f:<18} {imp:.3f}")


print("\n" + "=" * 70)
print("RESUMO EXECUTIVO")
print("=" * 70)
tot = con.execute(
    "SELECT SUM(casos_notificados) c, SUM(internacoes) i FROM gold_fato_crise"
).fetchone()
print(f"Total de casos notificados:  {tot[0]:,}")
print(f"Total de internacoes:        {tot[1]:,}")
print(f"\nBairros em nivel CRITICO:")
print(risco[risco["nivel_risco"] == "CRITICO"]
      [["bairro", "eta", "taxa_internacao_100k", "cluster"]].to_string(index=False))

print("\nSILVER em:", SILVER)
print("GOLD   em:", GOLD)
print("\nProximo passo: streamlit run dashboard/app.py")
