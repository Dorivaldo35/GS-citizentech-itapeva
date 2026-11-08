# Etapa 4 — Arquitetura da Solução (Medallion)

## Diagrama lógico

```
                    +--------------------------------------------------+
                    |                     FONTES                       |
                    |  SISAGUA  SIH-SUS  SINAN  INMET  ANA  SNIS  IBGE |
                    |      + Laudos IAL / Boletins Sabesp / Decretos   |
                    +------------------------+-------------------------+
                                             |
                                 download / API / scraping
                                             |
                    +------------------------v-------------------------+
                    |                       BRONZE                     |
                    |  CSV / PDF / JSON originais, sem transformacao   |
                    |         particionamento por fonte e data         |
                    +------------------------+-------------------------+
                                             |
                               PySpark + SQL (limpeza, tipagem,
                                 padronizacao, deduplicacao)
                                             |
                    +------------------------v-------------------------+
                    |                       SILVER                     |
                    |   Tabelas Delta/Parquet padronizadas por dominio |
                    |  qualidade_agua | saude | clima | saneamento |   |
                    |              municipios_dim | bairros_dim         |
                    +------------------------+-------------------------+
                                             |
                                Joins + Feature Engineering
                                             |
                    +------------------------v-------------------------+
                    |                        GOLD                      |
                    |   Modelo analitico (fatos + dimensoes + KPIs)    |
                    |     fato_crise_diario / indicador_risco_bairro / |
                    |            linha_tempo_crise / ranking_eta       |
                    +------------------------+-------------------------+
                                             |
                                             |
                    +------------------------v-------------------------+
                    |               CAMADA DE APRESENTACAO             |
                    |   Streamlit Dashboard  |  Analises SQL ad-hoc    |
                    |      Modelos ML (clusterizacao + previsao)        |
                    +--------------------------------------------------+
```

## Decisoes tecnicas

| Decisao | Justificativa |
|---|---|
| **Padrao Medallion** | Pedido do enunciado; separa responsabilidades e permite reprocessar camadas |
| **PySpark no processamento** | Atende o item 8 (Databricks/Spark); escala com SISAGUA e SIH-SUS historicos |
| **SQL nas camadas Silver e Gold** | Preferencia do autor; SQL e mais legivel para transformacoes relacionais e facilita revisao |
| **Parquet nas camadas Silver/Gold** | Columnar, comprimido, nativo no Spark e no Pandas; roda em qualquer ambiente |
| **Streamlit no dashboard** | Python puro, grátis, deploy trivial; roda com Pandas lendo Parquet |
| **Databricks Community Edition** | Ambiente gratuito com Spark pronto; nao precisa configurar cluster |
| **Gerador de dados sinteticos** | Permite validar o pipeline antes dos downloads reais terminarem |

## Qualidade, rastreabilidade e atualizacao

- **Qualidade.** Cada tabela Silver tem checagens: nulos em chaves, range de
  valores (ex.: pH entre 0-14), unicidade (`municipio+data+parametro`).
- **Rastreabilidade.** Cada registro Silver carrega `fonte_bronze` e
  `data_ingestao` (linhagem explicita).
- **Atualizacao.** Scripts `src/bronze/fetch_*.py` sao idempotentes: podem
  rodar diariamente sem duplicar; nome do arquivo bronze inclui timestamp.
- **Confiabilidade.** Divergencias entre fontes (IAL x Sabesp) sao preservadas
  em colunas separadas e so sao reconciliadas na Gold com regra documentada.

## Mapeamento fisico

```
data/
├── bronze/
│   ├── sisagua/anno=YYYY/*.csv
│   ├── sih_sus/mes=YYYY-MM/*.csv
│   ├── sinan/ano=YYYY/*.csv
│   ├── inmet/estacao=A714/*.csv
│   ├── snis/ano=YYYY/*.csv
│   ├── ibge/censo_2022/*.csv
│   └── crise_2026/
│       ├── laudos_ial/*.pdf
│       ├── boletins_sabesp/*.pdf
│       └── pontos_distribuicao.csv
├── silver/
│   ├── qualidade_agua_mensal.parquet
│   ├── saude_mensal_itapeva.parquet
│   ├── clima_diario_itapeva.parquet
│   ├── saneamento_anual.parquet
│   └── bairros_itapeva_dim.parquet
└── gold/
    ├── fato_crise_2026_diario.parquet
    ├── indicador_risco_bairro.parquet
    ├── linha_tempo_crise.parquet
    └── ranking_eta.parquet
```
