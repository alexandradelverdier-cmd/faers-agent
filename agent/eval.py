from agent import ask
from tools import run_query

T = "`alexandra-delverdier-perso.faers_dev"

TESTS = [
    (
        "Combien de cas y a-t-il au total dans les données ?",
        f"SELECT COUNT(*) AS nb_cas FROM {T}.fct_reports`",
    ),
    (
        "Quelle proportion des cas est grave ?",
        f"SELECT ROUND(100 * COUNTIF(is_serious) / COUNT(*), 1) AS pct_graves FROM {T}.fct_reports`",
    ),
    (
        "Combien de cas de décès ont été déclarés en France ?",
        f"SELECT COUNT(*) AS nb FROM {T}.fct_reports` WHERE occurrence_country = 'FR' AND is_death",
    ),
    (
        "Quels sont les 5 effets indésirables les plus déclarés pour le sémaglutide ?",
        f"""SELECT re.reaction_pt, COUNT(DISTINCT re.primaryid) AS nb
            FROM {T}.fct_report_reactions` re
            JOIN {T}.fct_report_drugs` d USING (primaryid)
            WHERE d.drug_role = 'primary_suspect' AND d.active_ingredient LIKE '%SEMAGLUTIDE%'
            GROUP BY 1 ORDER BY nb DESC LIMIT 5""",
    ),
    (
        "Quels sont les 10 principes actifs les plus souvent suspects principaux dans des cas de décès ?",
        f"""SELECT d.active_ingredient, COUNT(DISTINCT r.primaryid) AS nb
            FROM {T}.fct_reports` r
            JOIN {T}.fct_report_drugs` d USING (primaryid)
            WHERE r.is_death AND d.drug_role = 'primary_suspect' AND d.active_ingredient IS NOT NULL
            GROUP BY 1 ORDER BY nb DESC LIMIT 10""",
    ),
]

for i, (question, reference_sql) in enumerate(TESTS, start=1):
    print("=" * 80)
    print(f"TEST {i} : {question}\n")
    print("--- Réponse attendue (requête de référence) ---")
    print(run_query(reference_sql))
    print("\n--- Réponse de l'agent ---")
    print(ask(question))
    print()