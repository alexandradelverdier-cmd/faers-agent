"""Charge dans BigQuery les trimestres FAERS manquants (couche brute)."""
import io
import re
import sys
import zipfile
from datetime import date

import pandas as pd
import requests
from google.cloud import bigquery

PROJECT = "alexandra-delverdier-perso"
DATASET = "faers_raw_layer"
START_YEAR = 2022
URL = "https://fis.fda.gov/content/Exports/faers_ascii_{y}q{q}.zip"

# Seules les colonnes utilisées par dbt sont conservées (stockage réduit)
COLUMNS = {
    "drug": ["primaryid", "caseid", "drug_seq", "role_cod", "drugname", "prod_ai", "route"],
    "reac": ["primaryid", "caseid", "pt"],
    "outc": ["primaryid", "caseid", "outc_cod"],
    "demo": ["primaryid", "caseid", "caseversion", "event_dt", "init_fda_dt", "fda_dt",
             "sex", "age", "age_cod", "occr_country", "occp_cod"],
}

client = bigquery.Client(project=PROJECT)


def all_quarters():
    """Tous les trimestres de START_YEAR jusqu'au trimestre en cours."""
    today = date.today()
    current = (today.year, (today.month - 1) // 3 + 1)
    for y in range(START_YEAR, today.year + 1):
        for q in range(1, 5):
            if (y, q) <= current:
                yield y, q


def is_loaded(suffix: str) -> bool:
    try:
        client.get_table(f"{PROJECT}.{DATASET}.demo_{suffix}")
        return True
    except Exception:
        return False


def download(y: int, q: int):
    """Renvoie l'archive du trimestre, ou None si la FDA ne l'a pas encore publiée."""
    response = requests.get(URL.format(y=y, q=q), headers={"User-Agent": "Mozilla/5.0"}, timeout=300)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    try:
        return zipfile.ZipFile(io.BytesIO(response.content))
    except zipfile.BadZipFile:
        return None


def find_file(archive, prefix: str, yy: str, q: int):
    pattern = re.compile(rf"(^|/){prefix}{yy}q{q}\.txt$", re.IGNORECASE)
    return next((name for name in archive.namelist() if pattern.search(name)), None)


def read_file(archive, name: str, columns: list) -> pd.DataFrame:
    with archive.open(name) as f:
        df = pd.read_csv(
            f, sep="$", dtype=str, encoding="latin-1", quoting=3,
            usecols=lambda c: c.strip().lower() in columns, on_bad_lines="skip",
        )
    df.columns = [c.strip().lower() for c in df.columns]
    for c in columns:
        if c not in df.columns:
            df[c] = None
    return df[columns]


def load(df: pd.DataFrame, table: str):
    config = bigquery.LoadJobConfig(
        schema=[bigquery.SchemaField(c, "STRING") for c in df.columns],
        write_disposition="WRITE_TRUNCATE",
    )
    client.load_table_from_dataframe(df, f"{PROJECT}.{DATASET}.{table}", job_config=config).result()
    print(f"  {table} : {len(df):,} lignes")


def load_quarter(y: int, q: int, archive):
    yy, suffix = str(y)[2:], f"{str(y)[2:]}q{q}"

    for prefix in ["drug", "reac", "outc"]:
        name = find_file(archive, prefix, yy, q)
        if name is None:
            sys.exit(f"Fichier {prefix} introuvable dans l'archive {suffix}")
        load(read_file(archive, name, COLUMNS[prefix]), f"{prefix}_{suffix}")

    # Cas supprimés par la FDA (une liste de caseid)
    name = find_file(archive, "delete", yy, q)
    if name:
        with archive.open(name) as f:
            deleted = pd.read_csv(f, header=None, names=["caseid"], dtype=str, encoding="latin-1")
        load(deleted, f"deleted_{suffix}")

    # demo en dernier : sa présence signifie que le trimestre est complet
    name = find_file(archive, "demo", yy, q)
    if name is None:
        sys.exit(f"Fichier demo introuvable dans l'archive {suffix}")
    load(read_file(archive, name, COLUMNS["demo"]), f"demo_{suffix}")


def main():
    for y, q in all_quarters():
        suffix = f"{str(y)[2:]}q{q}"
        if is_loaded(suffix):
            print(f"{suffix} : déjà chargé")
            continue
        print(f"{suffix} : téléchargement...")
        archive = download(y, q)
        if archive is None:
            print(f"{suffix} : pas encore publié par la FDA. Fin du chargement.")
            break
        load_quarter(y, q, archive)


if __name__ == "__main__":
    main()