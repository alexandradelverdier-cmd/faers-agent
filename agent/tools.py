from google.cloud import bigquery

PROJECT = "alexandra-delverdier-perso"
DATASET = "faers_dev"
TABLES = ["fct_reports", "fct_report_drugs", "fct_report_reactions"]
MAX_BYTES = 1_000_000_000  # plafond de 1 Go scanné par requête
MAX_ROWS = 50              # nombre max de lignes renvoyées à l'agent

client = bigquery.Client(project=PROJECT)


def get_schema() -> str:
    """Décrit les tables, colonnes et descriptions dbt."""
    lines = []
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
    print(run_query(
        "SELECT drug_role, COUNT(*) AS nb "
        "FROM `alexandra-delverdier-perso.faers_dev.fct_report_drugs` "
        "GROUP BY drug_role ORDER BY nb DESC"
    ))