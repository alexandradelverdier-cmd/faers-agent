from google.cloud import bigquery

PROJECT = "alexandra-delverdier-perso"
DATASET = "faers_dev"
TABLES = ["fct_reports", "fct_report_drugs", "fct_report_reactions"]
MAX_BYTES = 5_000_000_000  # plafond de 5 Go scanné par requête
MAX_ROWS = 50              # nombre max de lignes renvoyées à l'agent


def make_client() -> bigquery.Client:
    """En ligne : le compte de service stocké dans les secrets Streamlit. En local : ton compte Google."""
    try:
        import streamlit as st
        from google.oauth2 import service_account
        info = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(project=PROJECT, credentials=credentials)
    except Exception:
        return bigquery.Client(project=PROJECT)


client = make_client()


def get_coverage() -> dict:
    """Premier et dernier trimestre présents dans les données."""
    sql = f"SELECT MIN(source_quarter) AS debut, MAX(source_quarter) AS fin FROM `{PROJECT}.{DATASET}.fct_reports`"
    row = list(client.query(sql).result())[0]
    return {"debut": row.debut, "fin": row.fin}


def get_schema() -> str:
    """Décrit la période couverte, les tables, colonnes et descriptions dbt."""
    coverage = get_coverage()
    lines = [f"Période couverte par les données : de {coverage['debut']} à {coverage['fin']}.", ""]
    for name in TABLES:
        table = client.get_table(f"{PROJECT}.{DATASET}.{name}")
        lines.append(f"## `{PROJECT}.{DATASET}.{name}` ({table.num_rows} lignes)")
        lines.append(table.description or "")
        for field in table.schema:
            lines.append(f"- {field.name} ({field.field_type}) : {field.description or ''}")
        lines.append("")
    return "\n".join(lines)


def run_query(sql: str) -> str:
    """Exécute une requête SELECT en lecture seule et renvoie le résultat en texte."""
    cleaned = sql.strip().rstrip(";")
    if not cleaned.lower().startswith(("select", "with")) or ";" in cleaned:
        return "Erreur : une seule requête SELECT est autorisée."

    config = bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES)
    try:
        rows = client.query(cleaned, job_config=config).result(max_results=MAX_ROWS)
    except Exception as e:
        return f"Erreur SQL : {e}"

    headers = [f.name for f in rows.schema]
    lines = [" | ".join(headers)]
    for row in rows:
        lines.append(" | ".join(str(v) for v in row.values()))
    return "\n".join(lines)


if __name__ == "__main__":
    print(get_schema())