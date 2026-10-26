import streamlit as st
from agent import ask

MAX_QUESTIONS = 2
EXAMPLES = [
    "Quels sont les 10 principes actifs les plus souvent suspects principaux dans des cas de décès ?",
    "Quels sont les 5 effets indésirables les plus déclarés pour le sémaglutide ?",
    "Quelle proportion des cas est grave ?",
]

st.set_page_config(page_title="Agent FAERS", page_icon="💊", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, .stApp, .stMarkdown, .stButton button, textarea, label {
        font-family: 'Inter', sans-serif !important;
    }
    .block-container { padding-top: 2rem; max-width: 860px; }
    .stMarkdown p, .stMarkdown li { font-size: 1.12rem; line-height: 1.65; }
    [data-testid="stToolbar"] { display: none; }

    /* Bandeau d'en-tête */
    .hero {
        background: linear-gradient(135deg, #0F766E 0%, #14B8A6 100%);
        color: white; padding: 2.2rem 2rem; border-radius: 18px;
        margin-bottom: 1.5rem; box-shadow: 0 10px 30px rgba(15, 118, 110, 0.25);
    }
    .hero-badge {
        display: inline-block; background: rgba(255, 255, 255, 0.18);
        padding: 0.25rem 0.8rem; border-radius: 999px;
        font-size: 0.85rem; letter-spacing: 0.04em;
    }
    .hero-title { font-size: 2.4rem; font-weight: 700; margin: 0.6rem 0 0.4rem 0; line-height: 1.2; }
    .hero-text { font-size: 1.15rem; color: #E6FFFB; line-height: 1.6; }

    /* Chiffres clés */
    .stats { display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; }
    .stat {
        flex: 1; min-width: 150px; background: #F0FDFA; border: 1px solid #CCFBF1;
        border-radius: 14px; padding: 1rem; text-align: center;
    }
    .stat b { display: block; font-size: 1.6rem; color: #0F766E; }
    .stat span { font-size: 0.95rem; color: #475569; }

    /* Zone de question */
    [data-testid="stForm"] {
        border: 1px solid #CCFBF1; border-radius: 16px; padding: 1.2rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
    }
    textarea { font-size: 1.1rem !important; }
    .stTextArea label p { font-size: 1.05rem !important; font-weight: 600; }
    .stFormSubmitButton button { padding: 0.6rem 1.6rem; border-radius: 10px; }
    .stFormSubmitButton button p { font-size: 1.05rem !important; font-weight: 600; }

    /* Exemples cliquables */
    div.stButton > button {
        width: 100%; justify-content: flex-start; text-align: left;
        border-radius: 12px; border: 1px solid #99F6E4; background: #F0FDFA;
        padding: 0.7rem 1rem; transition: all 0.15s;
    }
    div.stButton > button:hover { border-color: #0F766E; background: #CCFBF1; color: #0F766E; }
    div.stButton > button p { font-size: 1.02rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("À propos")
    st.markdown(
        """
        Projet portfolio d'**Alexandra Delverdier**, data analyst spécialisée en santé.

        **Comment ça marche**
        1. L'agent lit le schéma des tables et leur documentation métier
        2. Il écrit une requête SQL et l'exécute sur BigQuery
        3. Il interprète le résultat avec les précautions de la pharmacovigilance

        **Stack** : BigQuery, dbt, Python, API Claude, Streamlit

        [Voir le code sur GitHub](https://github.com/alexandradelverdier-cmd/faers-agent)
        """
    )

st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">FDA · FAERS · 1ER TRIMESTRE 2024</div>
        <div class="hero-title">💊 Agent de pharmacovigilance</div>
        <div class="hero-text">Posez une question en français sur les déclarations d'effets indésirables.
        L'agent écrit la requête SQL, l'exécute et interprète le résultat.</div>
    </div>
    <div class="stats">
        <div class="stat"><b>406 184</b><span>cas déclarés</span></div>
        <div class="stat"><b>1,9 M</b><span>lignes médicaments</span></div>
        <div class="stat"><b>1,4 M</b><span>effets indésirables</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "count" not in st.session_state:
    st.session_state.count = 0
if "history" not in st.session_state:
    st.session_state.history = []


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
    with st.form("question_form", clear_on_submit=True):
        question = st.text_area(
            "Votre question",
            placeholder="Ex : quels effets indésirables sont les plus déclarés pour la quétiapine ?",
            height=100,
        )
        submitted = st.form_submit_button("Poser la question", type="primary")
    if submitted and question.strip():
        run(question.strip())

    st.caption(f"Questions restantes : {remaining} sur {MAX_QUESTIONS}")
    st.markdown("**Ou essayez un exemple :**")
    for example in EXAMPLES:
        if st.button(example, key=example):
            run(example)
else:
    st.info("Vous avez utilisé vos 2 questions de démonstration. Merci d'avoir testé l'agent !")

for item in reversed(st.session_state.history):
    with st.container(border=True):
        st.markdown(f"**❓ {item['question']}**")
        st.markdown(item["answer"])
        for sql in item["sql"]:
            with st.expander("Voir la requête SQL"):
                st.code(sql, language="sql")

st.divider()
st.caption(
    "Données : FDA FAERS. Déclarations spontanées : un nombre de signalements ne prouve pas "
    "un lien de causalité. Cet outil ne fournit aucun conseil médical."
)