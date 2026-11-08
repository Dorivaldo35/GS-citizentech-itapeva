# Etapa 1 e 2 — Investigação e Definição do Problema

## 1. Contexto

Em **novembro de 2026**, o município de **Itapeva/SP** (microrregião do Alto
Paranapanema, aproximadamente 93 mil habitantes) foi declarado em **estado de
calamidade pública** após o **Instituto Adolfo Lutz (IAL)** confirmar a presença
do protozoário ***Cryptosporidium*** em amostras da água distribuída pela
concessionária **Sabesp**. O decreto classificou a situação como **desastre
biológico de veiculação hídrica de Nível III**.

A contaminação provocou um surto de **gastroenterites**, suspensão de aulas na
rede municipal, instalação de pontos de distribuição por **caminhões-pipa**,
preocupação com a aplicação do **Enem** na cidade e abertura de uma **Comissão
Especial de Inquérito (CEI)** pela Câmara Municipal. A Sabesp anunciou a
instalação de ultrafiltração nas Estações de Tratamento de Água (ETA) **Pilão**
e **Aranhas**, suspensão da tarifa por 30 dias e pontos de distribuição
gratuita. Contudo, há **divergência** entre os laudos: o IAL identificou o
parasita em 4 análises enquanto a Sabesp afirma não tê-lo detectado em suas
coletas de 27 e 29 de outubro.

## 2. Definição do problema

### 2.1 Problema

Déficit de informações integradas e acionáveis que permitam à Prefeitura, à CEI
da Câmara e à sociedade civil compreender a **dimensão, a origem geográfica, a
evolução temporal e os impactos** da contaminação por *Cryptosporidium* na água
de abastecimento de Itapeva.

### 2.2 Pessoas e grupos afetados

- **~93.000 habitantes** da área urbana atendidos pelas ETAs Pilão e Aranhas
- **Estudantes** da rede municipal (aulas suspensas) e **candidatos do Enem**
- **Pessoas em maior vulnerabilidade**: crianças < 5 anos, idosos > 60 anos,
  imunocomprometidos — grupos de risco para gastroenterite grave
- **Profissionais de saúde** e **gestores públicos** que precisam priorizar
  recursos

### 2.3 Dimensões a analisar

1. **Temporal** — quando sinais de qualidade começaram a se desviar antes da
   crise se tornar pública; evolução diária de casos e turbidez.
2. **Espacial (bairro)** — concentração de internações e de reclamações por
   ETA de origem (Pilão × Aranhas) e por bairro.
3. **Socioeconômica** — incidência por renda e cobertura domiciliar da rede.
4. **Operacional** — adequação da resposta (caminhões-pipa, pontos de
   distribuição) às áreas mais afetadas.
5. **Histórica** — se o SISAGUA já registrava não-conformidades reincidentes
   no município nos últimos anos.

### 2.4 Decisões que poderiam ser melhoradas com dados

- **Priorização de bairros** para intervenção emergencial e pontos de
  distribuição
- **Validação da divergência IAL × Sabesp** cruzando dados de qualidade com
  casos de saúde
- **Acompanhamento da eficácia** das medidas (ultrafiltração nas ETAs,
  suspensão tarifária)
- **Alocação de leitos e insumos** da rede municipal de saúde
- **Subsídio à CEI** com linha do tempo baseada em evidência
- **Protocolos futuros** de resposta rápida a desastres de veiculação hídrica

### 2.5 Informações necessárias

| Informação | Para apoiar qual decisão |
|---|---|
| Série histórica de qualidade da água (turbidez, cloro, coliformes) | Detecção precoce; subsídio à CEI |
| Internações e notificações por doenças de veiculação hídrica | Dimensionar impacto; alocar leitos |
| Mapa de ETAs e zonas atendidas | Priorizar bairros |
| População e vulnerabilidade por bairro | Focar resposta nos mais afetados |
| Precipitação e turbidez bruta | Correlacionar gatilho ambiental |
| Localização dos caminhões-pipa | Avaliar cobertura da resposta |
| Laudos IAL e boletins Sabesp | Reconstruir linha do tempo |

## 3. Justificativa

**Relevância social.** Trata-se de uma calamidade pública **em curso** no momento
da elaboração deste trabalho, afetando diretamente cerca de 93 mil pessoas e com
desdobramentos imediatos em saúde pública, educação e cidadania.

**Viabilidade por dados.** O caso dispõe de fontes públicas robustas e abertas
que permitem reconstruir o fenômeno:

- **SISAGUA** (Ministério da Saúde) publica a qualidade da água por município
  desde 2014, em CSV.
- **SIH-SUS / DATASUS** disponibiliza internações por CID (A00-A09 cobre
  gastroenterites) por mês/município.
- **SNIS** fornece histórico anual de saneamento (cobertura, perdas,
  tratamento) de Itapeva.
- **INMET BDMEP** e **ANA HidroWeb** publicam precipitação e vazão do manancial.
- **IBGE Censo 2022** fornece granularidade por setor censitário.
- **Laudos do IAL**, **boletins da Sabesp** e **decretos da Prefeitura** estão
  disponíveis em formato PDF / notícias oficiais.

**Adequação ao papel de CitizenTech.** A CEI e as decisões operacionais estão
ocorrendo **agora**. Um pipeline analítico produzido por uma organização de
tecnologia cívica pode contribuir diretamente para a transparência e para o
processo decisório — exatamente o espírito do enunciado da Global Solution.

**Originalidade analítica.** A combinação das fontes acima para este recorte
geográfico e temporal específico ainda não foi consolidada em um produto
integrado de dados, o que confere ao projeto valor analítico e social efetivo.
