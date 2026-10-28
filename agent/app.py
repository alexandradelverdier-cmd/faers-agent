import os

import streamlit as st

# En ligne, la clé API vient des secrets Streamlit. En local, du fichier .env.
try:
    os.environ.setdefault("ANTHROPIC_API_KEY", st.secrets["ANTHROPIC_API_KEY"])
except Exception:
    pass

from agent import ask
from tools import DATASET, PROJECT, TABLES, client, get_coverage

MAX_QUESTIONS = 2
EXAMPLES = [
    "Quels sont les 10 principes actifs les plus souvent suspects principaux dans des cas de décès ?",
    "Comment ont évolué les cas graves déclarés avec le sémaglutide depuis 2022 ?",
    "Quels sont les 5 effets indésirables les plus déclarés pour l'apixaban ?",
]

st.set_page_config(page_title="Agent FAERS", page_icon="💊", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

    :root {
        --teal: #0F766E;
        --teal-soft: #F0FDFA;
        --teal-line: #CCFBF1;
        --ink: #0F172A;
        --muted: #64748B;
        --line: #E8EDF3;
        --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.04), 0 1px 3px rgba(15, 23, 42, 0.06);
        --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.06), 0 2px 4px rgba(15, 23, 42, 0.04);
        --shadow-lg: 0 12px 32px rgba(15, 118, 110, 0.10), 0 4px 8px rgba(15, 23, 42, 0.04);
        --radius: 16px;
    }

    html, body, .stApp, .stMarkdown, .stButton button, textarea, label, input {
        font-family: 'DM Sans', sans-serif !important;
    }
    .stApp { background: linear-gradient(180deg, #FAFCFC 0%, #FFFFFF 40%); }
    .block-container { padding-top: 2.5rem; max-width: 780px; }
    .stMarkdown p, .stMarkdown li { font-size: 1rem; line-height: 1.65; color: #1E293B; }
    [data-testid="stToolbar"] { display: none; }

    /* Barre latérale */
    [data-testid="stSidebar"] { background: #F8FBFA; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown li { font-size: 0.92rem; line-height: 1.6; color: #334155; }
    [data-testid="stSidebar"] h2 { font-size: 1.05rem; font-weight: 700; color: var(--ink); }

    /* En-tête */
    .hero {
        position: relative; overflow: hidden;
        background: #FFFFFF; border: 1px solid var(--line); border-radius: 20px;
        padding: 2rem 2rem 1.7rem; margin-bottom: 1.3rem; box-shadow: var(--shadow-lg);
    }
    .hero::before {
        content: ""; position: absolute; top: -80px; right: -80px; width: 240px; height: 240px;
        background: radial-gradient(circle, rgba(20, 184, 166, 0.18) 0%, rgba(20, 184, 166, 0) 70%);
    }
    .hero-badge {
        display: inline-block; font-size: 0.72rem; font-weight: 600;
        letter-spacing: 0.08em; text-transform: uppercase; color: var(--teal);
        background: var(--teal-soft); border: 1px solid var(--teal-line);
        padding: 0.3rem 0.75rem; border-radius: 999px;
    }
    .hero-title {
        font-size: 2.05rem; font-weight: 700; color: var(--ink);
        letter-spacing: -0.025em; margin: 0.9rem 0 0.5rem; line-height: 1.15;
    }
    .hero-title span {
        background: linear-gradient(90deg, #0F766E 0%, #14B8A6 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    .hero-text { font-size: 1rem; color: #475569; line-height: 1.6; margin: 0; max-width: 560px; }
    .hero-note { font-size: 0.84rem; color: var(--muted); margin-top: 0.9rem; }

    /* Chiffres clés */
    .stats { display: flex; gap: 0.8rem; margin-bottom: 1.6rem; flex-wrap: wrap; }
    .stat {
        flex: 1; min-width: 140px; padding: 1rem 1.1rem;
        background: #FFFFFF; border: 1px solid var(--line); border-radius: var(--radius);
        box-shadow: var(--shadow-sm); transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stat:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
    .stat b { display: block; font-size: 1.4rem; font-weight: 700; color: var(--teal); letter-spacing: -0.01em; }
    .stat span { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }

    /* Formulaire */
    [data-testid="stForm"] {
        background: #FFFFFF; border: 1px solid var(--line); border-radius: var(--radius);
        padding: 1.2rem 1.3rem; box-shadow: var(--shadow-md);
    }
    textarea {
        font-size: 0.98rem !important; border-radius: 12px !important;
        transition: box-shadow 0.15s ease;
    }
    textarea:focus { box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.18) !important; }
    .stTextArea label p { font-size: 0.9rem !important; font-weight: 600; color: var(--ink); }
    .stFormSubmitButton button {
        border-radius: 10px; padding: 0.5rem 1.4rem; border: none;
        background: linear-gradient(135deg, #0F766E 0%, #0D9488 100%);
        box-shadow: 0 4px 12px rgba(15, 118, 110, 0.25);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stFormSubmitButton button:hover {
        transform: translateY(-1px); box-shadow: 0 6px 16px rgba(15, 118, 110, 0.32);
    }
    .stFormSubmitButton button p { font-size: 0.95rem !important; font-weight: 600; color: #FFFFFF; }

    /* Exemples */
    .examples-title {
        font-size: 0.78rem; font-weight: 600; color: var(--muted);
        text-transform: uppercase; letter-spacing: 0.06em; margin: 1.3rem 0 0.5rem;
    }
    div.stButton > button {
        width: 100%; justify-content: flex-start; text-align: left;
        background: #FFFFFF; border: 1px solid var(--line); border-radius: 12px;
        padding: 0.65rem 1rem; box-shadow: var(--shadow-sm);
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px); border-color: #99F6E4;
        background: var(--teal-soft); box-shadow: var(--shadow-md); color: var(--teal);
    }
    div.stButton > button:active { transform: translateY(0); box-shadow: var(--shadow-sm); }
    div.stButton > button p { font-size: 0.92rem !important; }

    /* Cartes de réponse */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF; border: 1px solid var(--line) !important;
        border-radius: var(--radius) !important; box-shadow: var(--shadow-md);
    }
    [data-testid="stExpander"] details {
        border-radius: 12px !important; border: 1px solid var(--line) !important;
    }
    .stCaption, [data-testid="stCaptionContainer"] { font-size: 0.82rem; color: var(--muted); }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=86400)
def load_stats():
    """Période couverte et nombre de lignes, recalculés au plus une fois par jour."""
    coverage = get_coverage()
    counts = {name: client.get_table(f"{PROJECT}.{DATASET}.{name}").num_rows for name in TABLES}
    return coverage, counts


def millions(n: int) -> str:
    return f"{n / 1_000_000:.1f} M".replace(".", ",")


coverage, counts = load_stats()

with st.sidebar:
    st.header("À propos")
    st.markdown(
        """
        Projet portfolio d'**Alexandra Delverdier**, analytics engineer spécialisée dans les données de santé.

        **Comment ça marche**
        1. L'agent lit le schéma des tables et leur documentation métier
        2. Il écrit une requête SQL et l'exécute sur BigQuery
        3. Il interprète le résultat avec les précautions de la pharmacovigilance

        **Stack** : BigQuery, dbt, Python, API Claude, Streamlit

        [Voir le code sur GitHub](https://github.com/alexandradelverdier-cmd/faers-agent)
        """
    )

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-badge">FDA FAERS · {coverage['debut']} → {coverage['fin']}</div>
        <div class="hero-title">Agent de <span>pharmacovigilance</span></div>
        <p class="hero-text">Posez une question en français ou en anglais sur les déclarations d'effets indésirables.
        L'agent écrit la requête SQL, l'exécute et interprète le résultat.</p>
        <div class="hero-note">Outil d'exploration destiné aux professionnels de santé.</div>
    </div>
    <div class="stats">
        <div class="stat"><b>{millions(counts['fct_reports'])}</b><span>cas uniques</span></div>
        <div class="stat"><b>{millions(counts['fct_report_drugs'])}</b><span>lignes médicaments</span></div>
        <div class="stat"><b>{millions(counts['fct_report_reactions'])}</b><span>effets indésirables</span></div>
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
            height=90,
        )
        submitted = st.form_submit_button("Poser la question", type="primary")
    if submitted and question.strip():
        run(question.strip())

    st.caption(f"Questions restantes : {remaining} sur {MAX_QUESTIONS}")
    st.markdown('<div class="examples-title">Ou essayez un exemple</div>', unsafe_allow_html=True)
    for example in EXAMPLES:
        if st.button(example, key=example):
            run(example)
else:
    st.info("Vous avez utilisé vos 2 questions de démonstration. Merci d'avoir testé l'agent !")

for item in reversed(st.session_state.history):
    with st.container(border=True):
        st.markdown(f"**{item['question']}**")
        st.markdown(item["answer"])
        for sql in item["sql"]:
            with st.expander("Voir la requête SQL"):
                st.code(sql, language="sql")

st.divider()
st.caption(
    "Données : FDA FAERS. Déclarations spontanées : un nombre de signalements ne prouve pas "
    "un lien de causalité. Cet outil ne fournit aucun conseil médical."
)