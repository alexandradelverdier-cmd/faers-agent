from dotenv import load_dotenv
import anthropic
from tools import get_schema, run_query

load_dotenv()
client = anthropic.Anthropic()
MODEL = "claude-haiku-5-5"
MAX_STEPS = 8  # nombre max d'allers-retours, pour éviter une boucle infinie

SYSTEM_PROMPT = """Tu es un assistant de pharmacovigilance qui répond à des questions sur les données FAERS (FDA Adverse Event Reporting System, 1er trimestre 2024) stockées dans BigQuery.

Méthode :
1. Commence toujours par appeler get_schema pour connaître les tables.
2. Écris une requête SQL BigQuery et exécute-la avec run_query. Utilise toujours le nom complet des tables entre backticks.
3. Si la requête échoue, lis l'erreur, corrige et réessaie.
4. Réponds en français, de façon concise, en citant les chiffres obtenus.

Règles métier :
- Pour associer un effet indésirable à un médicament, filtre sur drug_role = 'primary_suspect', sauf demande contraire.
- Regroupe les médicaments par active_ingredient plutôt que par drug_name.
- Les noms de médicaments sont en majuscules (ex : WHERE active_ingredient LIKE '%SEMAGLUTIDE%').
- Signale quand des termes de mésusage (Off label use, Drug ineffective...) dominent les résultats.
- FAERS contient des déclarations spontanées : un nombre de signalements ne prouve pas un lien de causalité et ne permet pas de calculer une fréquence. Rappelle-le brièvement quand c'est pertinent.
- Recopie les libellés (principes actifs, effets MedDRA) exactement tels qu'ils apparaissent dans les résultats, sans les reformuler. Tu peux ajouter une traduction française entre parenthèses.
- Tu ne donnes jamais de conseil médical individuel.
"""

TOOLS = [
    {
        "name": "get_schema",
        "description": "Renvoie la liste des tables FAERS disponibles, leurs colonnes et leurs descriptions métier.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "run_query",
        "description": "Exécute une requête SQL SELECT sur BigQuery et renvoie au maximum 50 lignes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "Une seule requête SQL BigQuery de type SELECT."}
            },
            "required": ["sql"],
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> str:
    if name == "get_schema":
        return get_schema()
    if name == "run_query":
        return run_query(tool_input["sql"])
    return f"Outil inconnu : {name}"


def ask(question: str) -> str:
    messages = [{"role": "user", "content": question}]

    for _ in range(MAX_STEPS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        # Claude a fini : on renvoie sa réponse
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        # Claude veut utiliser un ou plusieurs outils : on les exécute
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                detail = f" : {block.input['sql']}" if block.name == "run_query" else ""
                print(f"  → {block.name}{detail}")
                result = execute_tool(block.name, block.input)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
        messages.append({"role": "user", "content": tool_results})

    return "Désolé, je n'ai pas réussi à répondre en un nombre raisonnable d'étapes."


if __name__ == "__main__":
    while True:
        question = input("\nTa question (ou 'q' pour quitter) : ")
        if question.strip().lower() == "q":
            break
        print("\n" + ask(question))