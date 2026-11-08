"""
Gera dados sintéticos realistas para a Bronze, permitindo rodar o pipeline
sem esperar os downloads reais (SISAGUA, SIH-SUS, INMET, etc).

Os dados simulam o caso Itapeva/SP com um surto de gastroenterite em nov/2026
e uma elevação de turbidez na segunda quinzena de outubro/2026.

Execução:
    python -m src.utils.gera_dados_sinteticos
"""
from __future__ import annotations
import os
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
random.seed(42)

BASE = Path(__file__).resolve().parents[2]
BRONZE = BASE / "data" / "bronze"

COD_IBGE_ITAPEVA = 3522208

BAIRROS = [
    ("Centro",          "Pilao",   "renda_alta",   6200),
    ("Vila Isabel",     "Pilao",   "renda_media",  5800),
    ("Jardim Maringa",  "Pilao",   "renda_media",  5400),
    ("Vila Aparecida",  "Pilao",   "renda_baixa",  7100),
    ("Jardim Ferrari",  "Aranhas", "renda_media",  4900),
    ("Cidade Nova",     "Aranhas", "renda_baixa",  8300),
    ("Vila Sao Benedito","Aranhas","renda_baixa",  7600),
    ("Pilao Alto",      "Pilao",   "renda_alta",   3200),
    ("Jardim Grajau",   "Aranhas", "renda_baixa",  6900),
    ("Alto da Boa Vista","Pilao",  "renda_media",  4100),
    ("Jardim Pilao",    "Pilao",   "renda_baixa",  5500),
    ("Vila Nova",       "Aranhas", "renda_media",  4700),
]


def _ensure_dirs() -> None:
    for sub in ("sisagua", "sih_sus", "sinan", "inmet", "snis",
                "ibge", "crise_2026"):
        (BRONZE / sub).mkdir(parents=True, exist_ok=True)


def gera_dim_bairros() -> None:
    df = pd.DataFrame(
        BAIRROS, columns=["bairro", "eta", "classe_renda", "populacao"]
    )
    df["cod_ibge"] = COD_IBGE_ITAPEVA
    df["lat"] = -23.98 + RNG.normal(0, 0.015, len(df))
    df["lon"] = -48.87 + RNG.normal(0, 0.015, len(df))
    df["domicilios_rede_agua_pct"] = np.where(
        df["classe_renda"] == "renda_alta", 99,
        np.where(df["classe_renda"] == "renda_media", 95, 87),
    )
    df.to_csv(BRONZE / "ibge" / "bairros_itapeva.csv",
              index=False, encoding="utf-8")


def gera_sisagua() -> None:
    """Parâmetros de qualidade mensais (2015-2026) por ETA."""
    rows = []
    start = date(2015, 1, 1)
    end = date(2026, 11, 1)
    cur = start
    while cur <= end:
        for eta in ("Pilao", "Aranhas"):
            # ruido base
            cloro = RNG.normal(1.2, 0.2)
            turbidez = RNG.normal(0.6, 0.3)
            coli_tot = RNG.poisson(0.2)
            ecoli = RNG.poisson(0.05)
            # cenário de deterioracao em set-out 2026
            if (cur.year, cur.month) in [(2026, 9), (2026, 10), (2026, 11)]:
                turbidez += RNG.normal(1.8, 0.6) if eta == "Pilao" else RNG.normal(2.4, 0.7)
                cloro -= 0.3
                coli_tot += RNG.poisson(0.8)
                ecoli += RNG.poisson(0.3)
            rows.append({
                "cod_ibge": COD_IBGE_ITAPEVA,
                "municipio": "Itapeva",
                "uf": "SP",
                "ponto_coleta": f"ETA_{eta}",
                "eta": eta,
                "data_coleta": cur.isoformat(),
                "cloro_residual_mg_l": round(max(0, cloro), 3),
                "turbidez_ntu": round(max(0, turbidez), 3),
                "coliformes_totais_ufc": int(max(0, coli_tot)),
                "ecoli_ufc": int(max(0, ecoli)),
                "conformidade": "Conforme" if (cloro >= 0.2 and turbidez <= 5 and ecoli == 0) else "Nao conforme",
            })
        # proximo mes
        y, m = cur.year, cur.month
        cur = date(y + (m // 12), 1 if m == 12 else m + 1, 1)
    pd.DataFrame(rows).to_csv(
        BRONZE / "sisagua" / "sisagua_itapeva_2015_2026.csv",
        index=False, encoding="utf-8",
    )


def gera_sih_sus() -> None:
    """Internacoes mensais por CID (A00-A09, B15)."""
    rows = []
    start = date(2018, 1, 1)
    end = date(2026, 10, 1)
    cur = start
    while cur <= end:
        baseline = RNG.poisson(18)
        # surto novembro
        if (cur.year, cur.month) == (2026, 10):
            baseline += RNG.poisson(90)  # ja começa a subir no fim de outubro
        if (cur.year, cur.month) == (2026, 11):
            baseline += RNG.poisson(240)
        for cid in ["A00", "A01", "A02", "A04", "A08", "A09", "B15"]:
            n = max(0, int(RNG.normal(baseline / 7, 3)))
            rows.append({
                "cod_ibge_municipio": COD_IBGE_ITAPEVA,
                "municipio": "Itapeva",
                "uf": "SP",
                "mes_ano": cur.strftime("%Y-%m"),
                "cid10": cid,
                "n_internacoes": n,
                "obitos": max(0, int(RNG.poisson(n * 0.01))),
                "dias_permanencia_media": round(RNG.normal(3.5, 1.0), 1),
            })
        y, m = cur.year, cur.month
        cur = date(y + (m // 12), 1 if m == 12 else m + 1, 1)
    pd.DataFrame(rows).to_csv(
        BRONZE / "sih_sus" / "sih_itapeva_2018_2026.csv",
        index=False, encoding="utf-8",
    )


def gera_inmet() -> None:
    """Precipitacao e temperatura diaria estacao A714 Itapeva."""
    rows = []
    cur = date(2020, 1, 1)
    end = date(2026, 11, 30)
    while cur <= end:
        # media de 4 mm/dia, variavel sazonalmente; chuvas fortes em out-26
        base = max(0, RNG.gamma(1.1, 3.5))
        if (cur.year, cur.month) == (2026, 10) and cur.day >= 15:
            base = max(base, RNG.gamma(2.5, 8))  # eventos extremos
        temp = 18 + 7 * np.sin(2 * np.pi * (cur.timetuple().tm_yday / 365)) + RNG.normal(0, 2)
        umid = max(40, min(100, 70 + RNG.normal(0, 12)))
        rows.append({
            "estacao": "A714",
            "municipio": "Itapeva",
            "uf": "SP",
            "data": cur.isoformat(),
            "precipitacao_mm": round(base, 1),
            "temperatura_c": round(temp, 1),
            "umidade_pct": round(umid, 1),
        })
        cur += timedelta(days=1)
    pd.DataFrame(rows).to_csv(
        BRONZE / "inmet" / "inmet_a714_2020_2026.csv",
        index=False, encoding="utf-8",
    )


def gera_snis() -> None:
    """Indicadores anuais SNIS para Itapeva."""
    rows = []
    for ano in range(2015, 2024):
        rows.append({
            "ano": ano,
            "cod_ibge": COD_IBGE_ITAPEVA,
            "municipio": "Itapeva",
            "uf": "SP",
            "cobertura_agua_pct": 97 + RNG.normal(0, 0.5),
            "cobertura_esgoto_pct": 81 + (ano - 2015) * 0.6 + RNG.normal(0, 0.8),
            "perdas_distribuicao_pct": 32 - (ano - 2015) * 0.4 + RNG.normal(0, 1),
            "indice_tratamento_esgoto_pct": 72 + (ano - 2015) * 0.8 + RNG.normal(0, 1),
            "volume_tratado_m3": int(RNG.normal(14_000_000, 300_000)),
        })
    pd.DataFrame(rows).to_csv(
        BRONZE / "snis" / "snis_itapeva.csv",
        index=False, encoding="utf-8",
    )


def gera_crise_2026() -> None:
    """Internacoes diarias por bairro + pontos de distribuicao."""
    # internacoes por bairro no surto (out-nov 2026)
    rows = []
    cur = date(2026, 10, 1)
    end = date(2026, 11, 30)
    while cur <= end:
        for bairro, eta, classe, pop in BAIRROS:
            # risco relativo: Aranhas > Pilao, baixa renda > outros
            risco = 1.0
            if eta == "Aranhas":
                risco *= 1.8
            if classe == "renda_baixa":
                risco *= 1.6
            elif classe == "renda_alta":
                risco *= 0.7
            # evolucao do surto
            dias_desde_inicio = (cur - date(2026, 10, 20)).days
            if dias_desde_inicio < 0:
                nivel = RNG.poisson(0.1 * risco)
            elif dias_desde_inicio < 15:
                nivel = RNG.poisson(1.5 * risco * (dias_desde_inicio + 1) / 15)
            else:
                nivel = RNG.poisson(3.0 * risco)
            rows.append({
                "data": cur.isoformat(),
                "bairro": bairro,
                "eta": eta,
                "casos_notificados": int(nivel),
                "internacoes": int(RNG.binomial(nivel, 0.15)),
            })
        cur += timedelta(days=1)
    pd.DataFrame(rows).to_csv(
        BRONZE / "crise_2026" / "casos_por_bairro_diario.csv",
        index=False, encoding="utf-8",
    )

    # pontos de distribuicao de caminhao pipa
    pontos = []
    for bairro, eta, classe, pop in BAIRROS:
        # nem todo bairro tem; vamos simular que apenas 7 dos 12 tem
        if RNG.random() < 0.6:
            pontos.append({
                "bairro": bairro,
                "endereco_referencia": f"Escola Municipal {bairro}",
                "data_inicio": "2026-11-04",
                "veiculos_dia": RNG.integers(1, 4),
                "litros_dia_estimado": int(RNG.normal(20000, 4000)),
            })
    pd.DataFrame(pontos).to_csv(
        BRONZE / "crise_2026" / "pontos_distribuicao.csv",
        index=False, encoding="utf-8",
    )

    # laudos IAL (linha do tempo)
    laudos = [
        {"data_laudo": "2026-10-28", "ponto": "ETA Aranhas - saida", "agente": "Cryptosporidium", "resultado": "Detectado"},
        {"data_laudo": "2026-10-30", "ponto": "ETA Pilao - saida",   "agente": "Cryptosporidium", "resultado": "Detectado"},
        {"data_laudo": "2026-11-02", "ponto": "Rede - Centro",        "agente": "Cryptosporidium", "resultado": "Detectado"},
        {"data_laudo": "2026-11-05", "ponto": "Rede - Cidade Nova",   "agente": "Cryptosporidium", "resultado": "Detectado"},
    ]
    pd.DataFrame(laudos).to_csv(
        BRONZE / "crise_2026" / "laudos_ial.csv",
        index=False, encoding="utf-8",
    )


def main() -> None:
    _ensure_dirs()
    print("[1/6] Dimensao de bairros...")
    gera_dim_bairros()
    print("[2/6] SISAGUA (qualidade da agua)...")
    gera_sisagua()
    print("[3/6] SIH-SUS (internacoes)...")
    gera_sih_sus()
    print("[4/6] INMET (clima)...")
    gera_inmet()
    print("[5/6] SNIS (saneamento)...")
    gera_snis()
    print("[6/6] Crise 2026 (bairros, pontos, laudos)...")
    gera_crise_2026()
    print("\nOK. Dados sinteticos em data/bronze/")


if __name__ == "__main__":
    main()
