# Databricks notebook source
# MAGIC %md
# MAGIC # Pipeline Itapeva - Contaminacao por Cryptosporidium (nov/2026)
# MAGIC
# MAGIC Pipeline Medallion (Bronze -> Silver -> Gold) em PySpark + SQL para a GS.
# MAGIC
# MAGIC **Importacao no Databricks Community:**
# MAGIC 1. `File -> Import -> File` e selecione este `.py`
# MAGIC 2. Suba os CSVs de `data/bronze/` para `/FileStore/tables/itapeva/bronze/`
# MAGIC 3. Execute celula a celula
# MAGIC
# MAGIC **Execucao local (sem Databricks):**
# MAGIC ```
# MAGIC python notebooks/pipeline_itapeva.py
# MAGIC ```

# COMMAND ----------
# MAGIC %md
# MAGIC ## 0. Setup e deteccao de ambiente

# COMMAND ----------
import os
import sys
from pathlib import Path

try:
    # No Databricks a variavel `spark` ja existe
    spark  # type: ignore[name-defined]
    IS_DATABRICKS = True
    BRONZE = "/FileStore/tables/itapeva/bronze"
    SILVER = "/FileStore/tables/itapeva/silver"
    GOLD   = "/FileStore/tables/itapeva/gold"
except NameError:
    IS_DATABRICKS = False
    from pyspark.sql import SparkSession
    spark = (
        SparkSession.builder
        .appName("ItapevaPipeline")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    HERE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    ROOT = HERE.parent
    BRONZE = str(ROOT / "data" / "bronze")
    SILVER = str(ROOT / "data" / "silver")
    GOLD   = str(ROOT / "data" / "gold")
    Path(SILVER).mkdir(parents=True, exist_ok=True)
    Path(GOLD).mkdir(parents=True, exist_ok=True)

print(f"Ambiente: {'Databricks' if IS_DATABRICKS else 'Local'}")
print(f"BRONZE: {BRONZE}")
print(f"SILVER: {SILVER}")
print(f"GOLD:   {GOLD}")

from pyspark.sql import functions as F, Window
from pyspark.sql.types import IntegerType, DoubleType, StringType, DateType

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Bronze -> leitura dos arquivos brutos

# COMMAND ----------
def read_csv(path: str):
    return (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .option("encoding", "UTF-8")
        .csv(path)
    )

sisagua_raw  = read_csv(f"{BRONZE}/sisagua/sisagua_itapeva_2015_2026.csv")
sih_raw      = read_csv(f"{BRONZE}/sih_sus/sih_itapeva_2018_2026.csv")
inmet_raw    = read_csv(f"{BRONZE}/inmet/inmet_a714_2020_2026.csv")
snis_raw     = read_csv(f"{BRONZE}/snis/snis_itapeva.csv")
bairros_raw  = read_csv(f"{BRONZE}/ibge/bairros_itapeva.csv")
casos_raw    = read_csv(f"{BRONZE}/crise_2026/casos_por_bairro_diario.csv")
pontos_raw   = read_csv(f"{BRONZE}/crise_2026/pontos_distribuicao.csv")
laudos_raw   = read_csv(f"{BRONZE}/crise_2026/laudos_ial.csv")

print("Linhas Bronze:")
for nome, df in [("sisagua", sisagua_raw), ("sih", sih_raw), ("inmet", inmet_raw),
                 ("snis", snis_raw), ("bairros", bairros_raw),
                 ("casos", casos_raw), ("pontos", pontos_raw), ("laudos", laudos_raw)]:
    print(f"  {nome:>10}: {df.count():>7} linhas")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Silver -> padronizacao, tipagem e checagens
# MAGIC
# MAGIC Usamos **Spark SQL** (preferencia do autor) para transformacoes relacionais.

# COMMAND ----------
# registra Bronze como temp views para usar SQL
sisagua_raw.createOrReplaceTempView("bronze_sisagua")
sih_raw.createOrReplaceTempView("bronze_sih")
inmet_raw.createOrReplaceTempView("bronze_inmet")
snis_raw.createOrReplaceTempView("bronze_snis")
bairros_raw.createOrReplaceTempView("bronze_bairros")
casos_raw.createOrReplaceTempView("bronze_casos")
pontos_raw.createOrReplaceTempView("bronze_pontos")
laudos_raw.createOrReplaceTempView("bronze_laudos")

# COMMAND ----------
silver_qualidade = spark.sql("""
    SELECT
        CAST(cod_ibge AS INT)                     AS cod_ibge,
        municipio,
        uf,
        eta,
        CAST(data_coleta AS DATE)                 AS data_coleta,
        YEAR(data_coleta)                         AS ano,
        MONTH(data_coleta)                        AS mes,
        CAST(cloro_residual_mg_l AS DOUBLE)       AS cloro_residual_mg_l,
        CAST(turbidez_ntu AS DOUBLE)              AS turbidez_ntu,
        CAST(coliformes_totais_ufc AS INT)        AS coliformes_totais_ufc,
        CAST(ecoli_ufc AS INT)                    AS ecoli_ufc,
        conformidade,
        CASE
            WHEN cloro_residual_mg_l < 0.2 THEN 1
            WHEN turbidez_ntu > 5         THEN 1
            WHEN ecoli_ufc > 0            THEN 1
            ELSE 0
        END                                        AS flag_nao_conforme,
        'sisagua'                                  AS fonte_bronze,
        current_timestamp()                        AS data_ingestao
    FROM bronze_sisagua
""")
silver_qualidade.write.mode("overwrite").parquet(f"{SILVER}/qualidade_agua_mensal.parquet")
silver_qualidade.createOrReplaceTempView("silver_qualidade")
print(f"silver qualidade_agua: {silver_qualidade.count()} linhas")

# COMMAND ----------
silver_saude = spark.sql("""
    SELECT
        CAST(cod_ibge_municipio AS INT)   AS cod_ibge,
        municipio,
        uf,
        TO_DATE(CONCAT(mes_ano, '-01'), 'yyyy-MM-dd') AS data_ref,
        mes_ano,
        cid10,
        CASE
            WHEN cid10 LIKE 'A0%'  THEN 'Gastroenterites'
            WHEN cid10 = 'B15'     THEN 'Hepatite A'
            ELSE 'Outros'
        END                               AS grupo_cid,
        CAST(n_internacoes AS INT)        AS n_internacoes,
        CAST(obitos AS INT)               AS obitos,
        CAST(dias_permanencia_media AS DOUBLE) AS dias_permanencia_media,
        'sih_sus'                         AS fonte_bronze,
        current_timestamp()               AS data_ingestao
    FROM bronze_sih
""")
silver_saude.write.mode("overwrite").parquet(f"{SILVER}/saude_mensal_itapeva.parquet")
silver_saude.createOrReplaceTempView("silver_saude")
print(f"silver saude: {silver_saude.count()} linhas")

# COMMAND ----------
silver_clima = spark.sql("""
    SELECT
        estacao,
        municipio,
        uf,
        CAST(data AS DATE) AS data,
        CAST(precipitacao_mm AS DOUBLE)  AS precipitacao_mm,
        CAST(temperatura_c AS DOUBLE)    AS temperatura_c,
        CAST(umidade_pct AS DOUBLE)      AS umidade_pct,
        'inmet' AS fonte_bronze,
        current_timestamp() AS data_ingestao
    FROM bronze_inmet
""")
silver_clima.write.mode("overwrite").parquet(f"{SILVER}/clima_diario_itapeva.parquet")
silver_clima.createOrReplaceTempView("silver_clima")
print(f"silver clima: {silver_clima.count()} linhas")

# COMMAND ----------
silver_bairros = spark.sql("""
    SELECT
        CAST(cod_ibge AS INT) AS cod_ibge,
        bairro,
        eta,
        classe_renda,
        CAST(populacao AS INT) AS populacao,
        CAST(lat AS DOUBLE)    AS lat,
        CAST(lon AS DOUBLE)    AS lon,
        CAST(domicilios_rede_agua_pct AS DOUBLE) AS dom_rede_agua_pct,
        'ibge_censo' AS fonte_bronze
    FROM bronze_bairros
""")
silver_bairros.write.mode("overwrite").parquet(f"{SILVER}/bairros_itapeva_dim.parquet")
silver_bairros.createOrReplaceTempView("silver_bairros")
print(f"silver bairros: {silver_bairros.count()} linhas")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. Feature Engineering (PySpark + SQL)
# MAGIC
# MAGIC Novas variaveis para representar melhor o fenomeno:
# MAGIC - **chuva_acumulada_7d / 14d**: antecipa pico de turbidez bruta
# MAGIC - **dias_sem_conformidade**: pressao historica sobre a ETA
# MAGIC - **taxa_internacao_100k**: internacoes por 100 mil hab
# MAGIC - **indice_vulnerabilidade_bairro**: combina renda + populacao + rede

# COMMAND ----------
# features de clima (precipitacao acumulada)
w7  = Window.orderBy("data").rowsBetween(-6, 0)
w14 = Window.orderBy("data").rowsBetween(-13, 0)
clima_feat = (
    silver_clima
    .withColumn("chuva_acum_7d",  F.sum("precipitacao_mm").over(w7))
    .withColumn("chuva_acum_14d", F.sum("precipitacao_mm").over(w14))
)
clima_feat.createOrReplaceTempView("silver_clima_feat")

# features de qualidade: dias_desde_ultima_nc por ETA
w_eta = Window.partitionBy("eta").orderBy("data_coleta")
qual_feat = (
    silver_qualidade
    .withColumn("mes_ultima_nc",
        F.when(F.col("flag_nao_conforme") == 1, F.col("data_coleta")))
    .withColumn("mes_ultima_nc",
        F.last("mes_ultima_nc", ignorenulls=True).over(w_eta))
    .withColumn("dias_desde_nc",
        F.datediff(F.col("data_coleta"), F.col("mes_ultima_nc")))
)
qual_feat.createOrReplaceTempView("silver_qualidade_feat")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4. Gold -> tabelas analiticas prontas para uso

# COMMAND ----------
# 4.1 Fato diario da crise (out-nov 2026): casos por bairro + chuva do dia
fato_crise = spark.sql("""
    WITH casos AS (
        SELECT
            CAST(data AS DATE) AS data,
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
    JOIN silver_bairros b ON c.bairro = b.bairro
    LEFT JOIN silver_clima_feat cf ON c.data = cf.data
""")
fato_crise.write.mode("overwrite").parquet(f"{GOLD}/fato_crise_2026_diario.parquet")
fato_crise.createOrReplaceTempView("gold_fato_crise")
print(f"gold fato_crise: {fato_crise.count()} linhas")

# COMMAND ----------
# 4.2 Indicador de risco por bairro
indicador_risco = spark.sql("""
    WITH agg AS (
        SELECT
            bairro, eta, classe_renda, populacao,
            SUM(casos_notificados) AS total_casos,
            SUM(internacoes)       AS total_internacoes,
            SUM(internacoes) * 100000.0 / MAX(populacao) AS taxa_int_100k
        FROM gold_fato_crise
        WHERE data >= DATE '2026-10-20'
        GROUP BY bairro, eta, classe_renda, populacao
    )
    SELECT
        bairro, eta, classe_renda, populacao,
        total_casos, total_internacoes,
        ROUND(taxa_int_100k, 2) AS taxa_internacao_100k,
        CASE
            WHEN taxa_int_100k > 150 THEN 'CRITICO'
            WHEN taxa_int_100k > 80  THEN 'ALTO'
            WHEN taxa_int_100k > 30  THEN 'MEDIO'
            ELSE 'BAIXO'
        END AS nivel_risco
    FROM agg
    ORDER BY taxa_int_100k DESC
""")
indicador_risco.write.mode("overwrite").parquet(f"{GOLD}/indicador_risco_bairro.parquet")
indicador_risco.createOrReplaceTempView("gold_indicador_risco")
indicador_risco.show(truncate=False)

# COMMAND ----------
# 4.3 Linha do tempo da crise (laudos + internacoes semanais + chuva)
linha_tempo = spark.sql("""
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
    SELECT
        c.semana,
        c.casos,
        c.internacoes,
        ch.chuva_semanal
    FROM sem_casos c
    LEFT JOIN sem_chuva ch ON c.semana = ch.semana
    ORDER BY c.semana
""")
linha_tempo.write.mode("overwrite").parquet(f"{GOLD}/linha_tempo_crise.parquet")
linha_tempo.show(truncate=False)

# COMMAND ----------
# 4.4 Ranking ETA (Pilao vs Aranhas)
ranking_eta = spark.sql("""
    SELECT
        eta,
        SUM(casos_notificados)   AS casos_total,
        SUM(internacoes)         AS internacoes_total,
        SUM(populacao)           AS pop_total,
        ROUND(SUM(internacoes) * 100000.0 / SUM(populacao), 2) AS taxa_int_100k
    FROM gold_fato_crise
    WHERE data >= DATE '2026-10-20'
    GROUP BY eta
    ORDER BY taxa_int_100k DESC
""")
ranking_eta.write.mode("overwrite").parquet(f"{GOLD}/ranking_eta.parquet")
ranking_eta.show()

# COMMAND ----------
# MAGIC %md
# MAGIC ## 5. ML -> clusterizacao e previsao
# MAGIC
# MAGIC - **KMeans**: agrupar bairros por perfil (renda, populacao, taxa de internacao)
# MAGIC - **RandomForest**: prever internacoes do dia seguinte com base em chuva e casos recentes

# COMMAND ----------
# sai do Spark para Pandas (dataset e pequeno)
pdf_bairros = indicador_risco.toPandas()

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

X = pdf_bairros[["populacao", "total_casos", "taxa_internacao_100k"]].fillna(0)
X_scaled = StandardScaler().fit_transform(X)
km = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X_scaled)
pdf_bairros["cluster"] = km.labels_
print(pdf_bairros[["bairro", "eta", "classe_renda",
                   "taxa_internacao_100k", "nivel_risco", "cluster"]])

# COMMAND ----------
# previsao: regressao simples internacoes ~ chuva_acum_7d + casos_lag1
pdf_fato = fato_crise.toPandas().sort_values(["bairro", "data"])
pdf_fato["casos_lag1"] = pdf_fato.groupby("bairro")["casos_notificados"].shift(1).fillna(0)
pdf_fato["chuva_acum_7d"] = pdf_fato["chuva_acum_7d"].fillna(0)

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

feat = ["chuva_acum_7d", "casos_lag1", "populacao"]
X = pdf_fato[feat]
y = pdf_fato["internacoes"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
rf = RandomForestRegressor(n_estimators=200, random_state=42).fit(X_tr, y_tr)
y_pred = rf.predict(X_te)
print(f"MAE : {mean_absolute_error(y_te, y_pred):.3f}")
print(f"R^2 : {r2_score(y_te, y_pred):.3f}")
print("Importancia das features:")
for f, imp in zip(feat, rf.feature_importances_):
    print(f"  {f:<20} {imp:.3f}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 6. Resumo executivo no proprio notebook

# COMMAND ----------
print("=" * 70)
print("RESUMO EXECUTIVO - PIPELINE ITAPEVA (nov/2026)")
print("=" * 70)
total_casos = fato_crise.agg(F.sum("casos_notificados")).collect()[0][0]
total_int   = fato_crise.agg(F.sum("internacoes")).collect()[0][0]
print(f"\nTotal de casos notificados (out-nov/26): {total_casos}")
print(f"Total de internacoes:                     {total_int}")
print(f"\nBairros em nivel CRITICO:")
indicador_risco.filter(F.col("nivel_risco") == "CRITICO").show(truncate=False)
print("Camadas gravadas em:")
print(f"  SILVER: {SILVER}")
print(f"  GOLD:   {GOLD}")
print("\nProximo passo: rode o dashboard -> streamlit run dashboard/app.py")
