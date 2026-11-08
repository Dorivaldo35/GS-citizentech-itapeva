# Relatório Executivo — Crise Hídrica e Sanitária em Itapeva/SP
**(template — preencher ao final do pipeline)**

> Documento endereçado à Prefeitura, à CEI da Câmara Municipal e à Sabesp.
> Elaborado por CitizenTech, organização de tecnologia cívica.

---

## 1. O que os dados revelam sobre o problema

Entre **outubro e novembro de 2026**, Itapeva registrou um aumento expressivo
de **casos de gastroenterite** correlacionado temporalmente com a identificação
de ***Cryptosporidium*** pelo Instituto Adolfo Lutz na água distribuída pelas
ETAs **Pilão** e **Aranhas**.

Principais achados do pipeline:

- Total de casos notificados no período: **{{ total_casos }}**
- Total de internações registradas: **{{ total_internacoes }}**
- Taxa média de internação em bairros atendidos pela ETA mais afetada:
  **{{ taxa_pior_eta }}/100 mil hab**

## 2. Situações, regiões ou grupos que merecem maior atenção

Bairros classificados em **risco CRÍTICO** pelo indicador construído:

| Bairro | ETA | Classe de renda | Taxa/100k |
|---|---|---|---|
| {{ bairro_1 }} | | | |
| {{ bairro_2 }} | | | |

Grupos de maior vulnerabilidade identificados: **crianças < 5 anos** e
**famílias em domicílios com menor cobertura da rede**.

## 3. Padrões e tendências identificados

- **Gatilho climático:** 7–10 dias após eventos de chuva superior a 40 mm, a
  turbidez bruta se elevou (SISAGUA) e os casos começaram a crescer.
- **Concentração espacial:** a ETA **{{ eta_pior }}** concentra >2× a taxa de
  internação da outra ETA.
- **Alertas prévios:** o SISAGUA registrava não-conformidades reincidentes
  desde **{{ ano_inicio_alerta }}**, indicando que a crise não foi um ponto
  fora da curva isolado.

## 4. Decisões que podem ser tomadas

1. **Priorizar a resposta** nos bairros CRÍTICO/ALTO (listados no dashboard).
2. **Validar divergência IAL × Sabesp** com coletas pareadas no mesmo ponto
   e no mesmo dia.
3. **Protocolo climático:** monitoramento reforçado nos 10 dias seguintes a
   chuvas >40 mm.
4. **Revisar o plano de manutenção** da ETA mais afetada e cronograma de
   ultrafiltração.
5. **Transparência com a CEI:** publicar linha do tempo construída.

## 5. Resultados a acompanhar

| Indicador | Meta | Fonte |
|---|---|---|
| Casos semanais de gastroenterite | Queda sustentada por 4 semanas | SIH-SUS |
| Turbidez média pós-ETA | ≤ 1 NTU | SISAGUA |
| *E. coli* em saída da ETA | 0 UFC em 100% das coletas | SISAGUA |
| Cobertura da distribuição | 100% dos bairros CRÍTICO | Prefeitura |

---

**Limitações do estudo.** Período curto de observação; dependência de laudos
cuja divergência ainda não foi reconciliada; dados de saúde com até 30 dias de
defasagem no SIH-SUS.
