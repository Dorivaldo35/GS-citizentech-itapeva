"""
Baixa internacoes SIH-SUS para Itapeva/SP via TabNet (Datasus).

Observacao: o TabNet nao tem API publica. O caminho mais estavel e:
 1. Acessar http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sih/cnv/nrsp.def
 2. Filtrar: Linha = Municipio; Coluna = Mes/ano; Conteudo = Internacoes
 3. Filtrar por capitulo I CID-10 (A00-A09, B15)
 4. Exportar CSV e colocar em data/bronze/sih_sus/

Este script padroniza/enriquece o CSV exportado.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "data" / "bronze" / "sih_sus"
OUT.mkdir(parents=True, exist_ok=True)

COD_IBGE_ITAPEVA = 3522208


def padronizar(csv_tabnet: Path) -> None:
    df = pd.read_csv(csv_tabnet, sep=";", encoding="latin-1", skiprows=3)
    # Esperado TabNet colocar municipios na primeira coluna e meses nas demais
    df = df.rename(columns={df.columns[0]: "municipio"})
    df_long = df.melt(id_vars="municipio", var_name="mes_ano",
                      value_name="n_internacoes")
    df_long["cod_ibge_municipio"] = COD_IBGE_ITAPEVA
    df_long["uf"] = "SP"
    out = OUT / csv_tabnet.name.replace(".csv", "_padronizado.csv")
    df_long.to_csv(out, index=False, encoding="utf-8")
    print(f"OK -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="Caminho do CSV exportado do TabNet")
    args = ap.parse_args()
    padronizar(Path(args.csv))


if __name__ == "__main__":
    main()
