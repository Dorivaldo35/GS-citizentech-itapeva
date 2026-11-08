"""
Dashboard CitizenTech - Crise Hidrica e Sanitaria Itapeva/SP (nov/2026)

Execucao:
    streamlit run dashboard/app.py
"""
from __future__ import annotations
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"
SILVER = ROOT / "data" / "silver"
BRONZE = ROOT / "data" / "bronze"

st.set_page_config(
    page_title="CitizenTech - Itapeva/SP nov/2026",
    page_icon="💧",
    layout="wide",
)

# ------------------------------------------------------------------
# LOADERS
# ------------------------------------------------------------------
@st.cache_data
def load_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        st.error(f"Arquivo nao encontrado: {path.name}\n"
                 "Rode o pipeline primeiro: `python notebooks/pipeline_itapeva.py`")
        st.stop()
    return pd.read_parquet(path)


fato      = load_parquet(GOLD / "fato_crise_2026_diario.parquet")
risco     = load_parquet(GOLD / "indicador_risco_bairro.parquet")
tempo     = load_parquet(GOLD / "linha_tempo_crise.parquet")
eta       = load_parquet(GOLD / "ranking_eta.parquet")
qualidade = load_parquet(SILVER / "qualidade_agua_mensal.parquet")

# ------------------------------------------------------------------
# HEADER
# ------------------------------------------------------------------
st.title("💧 CitizenTech — Crise Hídrica e Sanitária")
st.subheader("Itapeva/SP — Contaminação por *Cryptosporidium* (novembro/2026)")
st.caption(
    "Pipeline Big Data & Analytics (Medallion) — Global Solution FIAP 2026.2"
)

# KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Casos notificados", f"{int(fato['casos_notificados'].sum()):,}")
k2.metric("Internações", f"{int(fato['internacoes'].sum()):,}")
criticos = (risco["nivel_risco"] == "CRITICO").sum()
k3.metric("Bairros em risco CRÍTICO", int(criticos))
k4.metric("População exposta", f"{int(risco['populacao'].sum()):,}")

st.divider()

# ------------------------------------------------------------------
# ABAS
# ------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 Linha do tempo", "🗺️ Bairros em risco",
     "🏭 Pilão × Aranhas", "🧪 Qualidade histórica",
     "📋 Recomendações"]
)

# ------------------------------------------------------------------
with tab1:
    st.markdown("### Evolução semanal: casos, internações e chuva")
    fig = px.line(
        tempo, x="semana", y=["casos", "internacoes"],
        markers=True,
        labels={"value": "Quantidade", "semana": "Semana", "variable": ""},
    )
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.bar(
        tempo, x="semana", y="chuva_semanal",
        labels={"chuva_semanal": "Chuva semanal (mm)", "semana": "Semana"},
        title="Precipitação semanal (INMET A714)",
    )
    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------------------------
with tab2:
    st.markdown("### Taxa de internação por 100 mil habitantes, por bairro")
    df = risco.sort_values("taxa_internacao_100k", ascending=True)
    fig = px.bar(
        df, x="taxa_internacao_100k", y="bairro",
        color="nivel_risco",
        color_discrete_map={
            "CRITICO": "#b91c1c", "ALTO": "#ea580c",
            "MEDIO": "#ca8a04",   "BAIXO": "#16a34a",
        },
        orientation="h",
        hover_data=["eta", "classe_renda", "populacao",
                    "total_casos", "total_internacoes"],
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Tabela completa")
    st.dataframe(
        risco.sort_values("taxa_internacao_100k", ascending=False),
        use_container_width=True, hide_index=True,
    )

# ------------------------------------------------------------------
with tab3:
    st.markdown("### Comparativo entre as ETAs")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            eta, x="eta", y="taxa_int_100k", color="eta",
            labels={"taxa_int_100k": "Internações por 100k", "eta": "ETA"},
            title="Taxa de internação por ETA",
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(
            eta, x="eta", y="casos_total", color="eta",
            labels={"casos_total": "Casos totais", "eta": "ETA"},
            title="Casos totais por ETA",
        )
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(eta, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------
with tab4:
    st.markdown("### Turbidez mensal 2015–2026 (SISAGUA)")
    qual = qualidade.copy()
    qual["mes_ano"] = pd.to_datetime(qual["data_coleta"]).dt.to_period("M").dt.to_timestamp()
    agg = qual.groupby(["mes_ano", "eta"])[["turbidez_ntu", "cloro_residual_mg_l"]].mean().reset_index()
    fig = px.line(
        agg, x="mes_ano", y="turbidez_ntu", color="eta",
        labels={"mes_ano": "Mês", "turbidez_ntu": "Turbidez média (NTU)"},
        title="Turbidez por ETA",
    )
    fig.add_hline(y=5, line_dash="dash", line_color="red",
                  annotation_text="Limite 5 NTU (MS 888/2021)")
    st.plotly_chart(fig, use_container_width=True)

    nc = qual.groupby("ano", as_index=False)["flag_nao_conforme"].sum()
    fig = px.bar(nc, x="ano", y="flag_nao_conforme",
                 labels={"flag_nao_conforme": "Coletas fora do padrão"},
                 title="Não-conformidades por ano")
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
with tab5:
    st.markdown("## 📋 Recomendações para tomada de decisão")
    st.markdown("""
Com base nas análises do pipeline:

1. **Priorizar bairros CRÍTICO e ALTO** na distribuição de água e no reforço
   assistencial. A aba "Bairros em risco" mostra o ranking atualizado.

2. **Investigar sistematicamente a ETA com maior taxa de internação** (ver
   aba "Pilão × Aranhas"). Divergência IAL × Sabesp deve ser dirimida com
   coletas pareadas.

3. **Reforçar monitoramento após chuvas intensas (>40 mm)** — a correlação com
   picos de turbidez justifica alerta antecipado.

4. **Revisar histórico SISAGUA** — qualquer tendência crescente de
   não-conformidade sugere que o alerta poderia ter vindo antes.

5. **Acompanhar indicadores** semanalmente: casos novos, internações,
   turbidez por ETA e cobertura dos pontos de distribuição.
""")

# ------------------------------------------------------------------
st.divider()
st.caption("Projeto acadêmico — dados sintéticos realistas até a integração "
           "com as fontes reais (SISAGUA, SIH-SUS, INMET, ANA, SNIS).")
