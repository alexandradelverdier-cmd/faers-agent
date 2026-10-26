import streamlit as st
from agent import ask

MAX_QUESTIONS = 2
EXAMPLES = [
    "Quels sont les 10 principes actifs les plus souvent suspects principaux dans des cas de décès ?",
    "Quels sont les 5 effets indésirables les plus déclarés pour le sémaglutide ?",
    "Quelle proportion des cas est grave ?",
]

st.set_page_config(page_title="Agent FAERS", page_icon="💊")
st.title("💊 Agent de pharmacovigilance FAERS")
st.caption(
    "Pose une question en français sur les déclarations d'effets indésirables reçues par la FDA "
    "(1er trimestre 2024). L'agent écrit le SQL, l'exécute sur BigQuery et interprète le résultat."
)

if "count" not in st.session_state:
    st.session_state.count = 0
if "history" not in st.session_state:
    st.session_state.history = []

# Historique des échanges
for item in st.session_state.history:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant"):
        for sql in item["sql"]:
            with st.expander("Voir la requête SQL générée"):
                st.code(sql, language="sql")
        st.markdown(item["answer"])


def run(question: str):
    steps = []

    def on_step(name, tool_input):
        if name == "run_query":
            steps.append(tool_input["sql"])

    with st.spinner("L'agent analyse les données..."):
        answer = ask(question, on_step=on_step)
    st.session_state.history.append({"question": question, "sql": steps, "answer": answer})
    st.session_state.count += 1
    st.rerun()


remaining = MAX_QUESTIONS - st.session_state.count

if remaining > 0:
    st.write(f"Questions restantes : **{remaining}**")
    st.write("Exemples :")
    for example in EXAMPLES:
        if st.button(example):
            run(example)
    question = st.chat_input("Ta question...")
    if question:
        run(question)
else:
    st.info("Tu as utilisé tes 2 questions de démonstration. Merci d'avoir testé l'agent !")

st.divider()
st.caption(
    "Données : FDA FAERS. Déclarations spontanées : un nombre de signalements ne prouve pas "
    "un lien de causalité. Cet outil ne fournit aucun conseil médical."
)