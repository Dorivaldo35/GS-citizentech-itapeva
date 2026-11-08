# CitizenTech — Crise de Contaminação da Água em Itapeva/SP (nov/2026)

Projeto da **Global Solution 2026.2 — Big Data & Analytics** (FIAP).
Pipeline de dados em arquitetura Medallion (Bronze → Silver → Gold) para investigar
a contaminação por *Cryptosporidium* na água de abastecimento de Itapeva/SP e
subsidiar decisões da Prefeitura, da CEI da Câmara Municipal e da Sabesp.

## Como executar

```bash
# 1. ambiente virtual
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. gerar dados sintéticos (realistas) para testar o pipeline hoje
python -m src.utils.gera_dados_sinteticos

# 3. rodar o pipeline (local, via PySpark)
python notebooks/pipeline_itapeva.py

# 4. abrir o dashboard
streamlit run dashboard/app.py
```

## Como importar no Databricks Community

1. `File → Import` → arraste `notebooks/pipeline_itapeva.py`
2. Databricks reconhece as células (`# COMMAND ----------`) e abre como notebook
3. Faça upload dos CSVs de `data/bronze/` no DBFS (`/FileStore/tables/itapeva/bronze/`)
4. Execute célula a célula

## Estrutura

```
GS/
├── docs/          Documentação (etapas 1-9 do enunciado)
├── notebooks/     Notebook Databricks (orquestrador)
├── src/           Scripts Python (ingestão + utilidades)
├── sql/           Queries SQL (Silver, Gold e Analytics)
├── dashboard/     App Streamlit
├── data/          Dados brutos e processados (ignorado no git)
└── config/        Configuração de fontes
```

## Mapeamento com o enunciado da GS

| Etapa enunciado | Entregável |
|---|---|
| 1. Investigação do problema | `docs/01_investigacao_problema.md` |
| 2. Definição | mesmo documento |
| 3. Catálogo de dados | `docs/02_catalogo_dados.md` |
| 4. Arquitetura | `docs/03_arquitetura_medallion.md` |
| 5. Feature Engineering | `notebooks/pipeline_itapeva.py` (seção Silver) |
| 6. Analytics e indicadores | `sql/04_gold_indicadores.sql` + `sql/05_analytics_perguntas.sql` |
| 7. Análises avançadas (ML) | `notebooks/pipeline_itapeva.py` (seção ML) |
| 8. Databricks + Spark | notebook roda em Databricks Community Edition |
| 9. Recomendações | `docs/09_relatorio_executivo_template.md` + dashboard |
