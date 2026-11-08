# Etapa 3 — Catálogo de Dados

## Visão geral

O pipeline combina **8 fontes** de dados públicos oficiais. Nenhuma fonte
isolada responde a todas as perguntas do problema; a integração é necessária
para construir indicadores e análises consistentes.

## Fontes

### F1. SISAGUA — Qualidade da água para consumo humano
- **Órgão:** Ministério da Saúde (SVS / CGVAM)
- **Endereço:** https://dados.gov.br/dados/conjuntos-dados/qualidade-da-agua-para-consumo-humano
- **Formato / Frequência:** CSV anual (publicação mensal dos dados)
- **Granularidade:** ponto de coleta × mês
- **Atributos relevantes:** `cod_ibge`, `municipio`, `forma_abastecimento`,
  `ponto_coleta`, `data_coleta`, `parametro` (cloro residual, turbidez,
  coliformes totais, E. coli), `valor`, `conformidade`
- **Janela:** 2015-01 a 2026-11
- **Uso no projeto:** série histórica de qualidade + identificação de
  não-conformidades anteriores à crise

### F2. SIH-SUS — Internações hospitalares (SUS)
- **Órgão:** Ministério da Saúde / DATASUS
- **Endereço:** http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sih/cnv/nrsp.def
- **Formato / Frequência:** CSV mensal (TabNet)
- **Granularidade:** mês × município × CID-10
- **Atributos relevantes:** `cod_ibge_municipio`, `mes_ano`, `cid10`,
  `faixa_etaria`, `sexo`, `n_internacoes`, `obitos`, `dias_permanencia`
- **CIDs-alvo:** A00-A09 (gastroenterites), B15 (hepatite A)
- **Janela:** 2018-01 a 2026-10 (SIH tem atraso de ~1 mês)
- **Uso:** dimensionar impacto epidemiológico e comparar com histórico

### F3. SINAN — Agravos notificáveis
- **Órgão:** Ministério da Saúde / DATASUS
- **Endereço:** https://opendatasus.saude.gov.br/dataset/sinan
- **Formato:** CSV anual
- **Uso:** casos leves (não internados) de doenças de veiculação hídrica

### F4. INMET BDMEP — Meteorologia
- **Órgão:** INMET
- **Endereço:** https://bdmep.inmet.gov.br/
- **Estação:** A714 (Itapeva/SP, automática)
- **Atributos:** `data`, `hora`, `precipitacao_mm`, `temp_c`, `umidade_pct`
- **Uso:** gatilho climático (chuvas intensas → turbidez bruta)

### F5. ANA HidroWeb — Hidrologia
- **Órgão:** Agência Nacional de Águas
- **Endereço:** https://www.snirh.gov.br/hidroweb/
- **Uso:** vazão e nível do manancial captado pelas ETAs

### F6. SNIS — Saneamento histórico
- **Órgão:** Ministério das Cidades
- **Endereço:** http://app4.mdr.gov.br/serieHistorica/
- **Atributos relevantes:** `ano`, `cod_ibge`, `cobertura_agua_pct`,
  `cobertura_esgoto_pct`, `perdas_distribuicao_pct`, `volume_tratado_m3`,
  `indice_tratamento_esgoto_pct`
- **Uso:** linha de base estrutural de Itapeva

### F7. IBGE — Censo 2022 e Setores Censitários
- **Órgão:** IBGE
- **Atributos relevantes:** população por bairro, renda domiciliar,
  domicílios ligados à rede de água/esgoto
- **Uso:** dimensão socioeconômica; ponderação de indicadores

### F8. Fontes da crise 2026 (dados não estruturados)
- **Laudos IAL** (PDF) — datas, pontos de coleta, parâmetros
- **Boletins Sabesp** (HTML/PDF) — status de ETAs, pontos de distribuição
- **Decretos / Comunicados da Prefeitura** (PDF) — medidas, escolas, datas
- **Lista de pontos de caminhão-pipa** (comunicados oficiais) — endereço, dias

## Avaliação de confiabilidade

| Fonte | Confiabilidade | Observação |
|---|---|---|
| SISAGUA | Alta | Oficial, com regras de validação |
| SIH-SUS | Alta | Padrão-ouro de internações |
| SINAN | Média | Subnotificação conhecida; usar como complemento |
| INMET | Alta | Estação oficial automática |
| ANA | Alta | Mas pode ter lacunas em telemetria |
| SNIS | Alta | Padrão nacional (declarado pela concessionária) |
| IBGE | Alta | Censo mais recente |
| Laudos/boletins 2026 | A validar | Ponto crítico; cruzar com qualidade registrada |

## Estratégia de aquisição

1. **Automatizada (scripts em `src/bronze/`):** SISAGUA, SIH-SUS, INMET, SNIS
2. **Download manual + ingestão:** IBGE setores, ANA HidroWeb
3. **Scraping / extração de PDF:** laudos IAL, boletins Sabesp, decretos
4. **Gerador sintético (`src/utils/gera_dados_sinteticos.py`):** amostra
   realista para validar o pipeline enquanto os dados reais são coletados
