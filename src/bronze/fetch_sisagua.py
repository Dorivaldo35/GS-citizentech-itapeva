"""
Baixa o SISAGUA (qualidade da agua de consumo humano) do dados.gov.br.

Por padrao filtra Itapeva/SP. Pode ser estendido para outros municipios.

Execucao:
    python -m src.bronze.fetch_sisagua --ano 2024
"""
from __future__ import annotations
import argparse
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "data" / "bronze" / "sisagua"
OUT.mkdir(parents=True, exist_ok=True)

COD_IBGE_ITAPEVA = 3522208

# O portal publica datasets anuais. O caminho pode mudar com o tempo.
# Documentacao: https://dados.gov.br/dados/conjuntos-dados/qualidade-da-agua-para-consumo-humano
# Consulte a pagina para a URL do CSV do ano desejado.


def baixar_csv(url: str, destino: Path) -> None:
    print(f"Baixando {url}...")
    r = requests.get(url, timeout=120, stream=True)
    r.raise_for_status()
    with open(destino, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"OK -> {destino}")


def filtrar_itapeva(csv_path: Path) -> None:
    print(f"Filtrando Itapeva/SP em {csv_path.name}...")
    df = pd.read_csv(csv_path, sep=";", encoding="latin-1", low_memory=False)
    # Nome da coluna de codigo IBGE varia: ajuste conforme o dataset
    possiveis = [c for c in df.columns if "ibge" in c.lower()]
    col = possiveis[0] if possiveis else None
    if col:
        df = df[df[col].astype(str).str.startswith(str(COD_IBGE_ITAPEVA))]
    filtrado = csv_path.with_name(f"itapeva_{csv_path.name}")
    df.to_csv(filtrado, index=False, encoding="utf-8")
    print(f"OK -> {filtrado} ({len(df)} linhas)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="URL do CSV do SISAGUA para o ano")
    ap.add_argument("--ano", type=int, default=2024)
    args = ap.parse_args()

    if not args.url:
        print("Informe a URL do CSV com --url. Consulte:")
        print("  https://dados.gov.br/dados/conjuntos-dados/qualidade-da-agua-para-consumo-humano")
        return

    destino = OUT / f"sisagua_{args.ano}.csv"
    baixar_csv(args.url, destino)
    filtrar_itapeva(destino)


if __name__ == "__main__":
    main()
