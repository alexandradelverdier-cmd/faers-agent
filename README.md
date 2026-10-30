# FAERS pharmacovigilance agent

An AI agent that answers questions on FDA adverse drug event reports. Ask a question in English or French, and the agent writes the SQL query, runs it on BigQuery and explains the result.

**Live demo:** [faers-agent.streamlit.app](https://faers-agent.streamlit.app)

## Why I built this

I worked as a nurse for nearly eight years, in hospitals and then in private practice. I often saw pharmacists rely solely on the Vidal (the French drug reference) when looking up information on a drug. Other sources exist, but they are rarely easy to use. Pharmacovigilance moves fast: reports are added, corrected or removed every day, and pharmaceutical companies, pharmacies and care facilities all need easy access to this data.

Later, while working in medtech, I met many pharmacy professionals who were teaching themselves data skills, since working with this kind of data isn't part of their initial training. I wanted to give them a tool that doesn't require learning SQL.

My background as a nurse helped at every step. I know the questions healthcare professionals ask, the time pressure they face when making decisions, and what will actually be useful to them. It's also what helped me spot several traps in the data.

## Who it's for

People who need quick, flexible answers from pharmacovigilance data without writing SQL queries: medical affairs and regulatory teams, pharmacovigilance analysts, pharmacy students, researchers and small teams without specialised safety software. It is not designed for patients and does not give any medical advice.

Tools already exist: the FDA offers a public FAERS dashboard, and large safety teams use dedicated signal detection software. This project explores something different: answering free-form questions in plain language, with every figure backed by a visible SQL query and pharmacovigilance rules built into the agent. The same approach can be applied to an internal safety database.

## Why not just ask ChatGPT?

A general chatbot doesn't have FAERS data. Ask it how many deaths were reported with apixaban in 2025, and it will answer from memory, with numbers that may be outdated or made up. The raw files are also far too large to paste into a conversation.

Here, every number comes from a real query on 6.4 million cleaned cases, and the query is always shown, so anyone can check where a result comes from. That matters in a regulated field. Pharmacovigilance rules are built into the agent: it focuses on the primary suspect drug, flags misuse terms and never implies causality.

FAERS is just the demo. The same approach works on an internal safety database that can't be shared with a public chatbot.

## The data: why FAERS

FAERS (FDA Adverse Event Reporting System) collects adverse event reports submitted to the FDA by drug companies, healthcare professionals and patients from all over the world, including France.

It's one of the few large pharmacovigilance databases published case by case, free of charge, every quarter. The French national database is only publicly available in aggregated form, EudraVigilance doesn't allow full downloads, and detailed access to VigiBase (WHO) is restricted.

The project covers data from 2022 up to the latest quarter published by the FDA.

## How it works

```
FDA quarterly files
        ↓  ingestion/load_faers.py
BigQuery raw layer (one table per quarter)
        ↓  dbt: staging, then marts, with tests
BigQuery analytics tables
        ↓  agent/tools.py
Agent (Claude API)
        ↓
Streamlit interface
```

The agent has two tools: one reads the table documentation (written in dbt and copied to BigQuery), the other runs a read-only query with a cap on scanned data. The agent decides on its own when to use them and fixes its query if it fails.

## Challenges I ran into

- **A zigzag curve.** When I plotted semaglutide reports over time, the curve swung up and down from one quarter to the next. My first guess was a date issue: I was counting each case in the quarter of its latest update instead of its first report. I fixed that and reloaded the data, but the curve barely changed. Splitting serious and non-serious cases revealed the real cause: serious cases grow steadily, while non-serious cases jump from a few dozen to several thousand between quarters. Companies must submit serious, unexpected cases quickly, but non-serious cases are often bundled into periodic reports. To assess a trend, you need to look at serious cases first, and the agent now follows that rule.
- **Duplicate versions.** Updated cases reappear in later quarters. Out of 7.6 million raw reports, 1.1 million (about 15%) were older versions or cases withdrawn by the FDA.
- **Out-of-scope questions.** A public demo can be used by anyone. When asked "Can I stop my sertraline if I feel nauseous?", the agent initially answered with a percentage of reports that a patient could mistake for a risk. It now refuses to run queries for personal medical questions, refers the person to their doctor or pharmacist, and provides the French suicide prevention line (3114) when relevant.
- **Drug labels.** Combination products are written as `FENTANYL\FENTANYL CITRATE`, and the agent tended to reword them. It now copies labels exactly as they appear.

## Some technical choices

- **Everything is stored as text in the raw layer.** FDA files sometimes change format. Type conversions happen in dbt, so a load doesn't fail because of a badly guessed type.
- **One table per quarter.** dbt reads them all at once using BigQuery wildcard tables, so new quarters are automatically included without code changes.
- **Resumable loads.** The main table is loaded last and acts as a marker: an interrupted quarter is simply reloaded.
- **Zero running cost.** Only the columns I use are loaded, and tables are partitioned and clustered to limit the amount of data scanned.
- **Agent evaluation.** A set of questions with known answers, checked against queries I wrote by hand, makes sure the agent's numbers are right.

## Data updates

The GitHub Actions workflow `update_faers.yml` loads new quarters, rebuilds the tables and runs the tests. It's triggered manually from the Actions tab. To run it automatically every month, uncomment the two `schedule` lines in the file.

## Limitations

- Reports are spontaneous: the number of reports does not establish causality and cannot be used to calculate incidence or risk. Under-reporting and media attention also skew the numbers.
- Companies often bundle non-serious cases into periodic reports, which creates artificial spikes. Trends are more reliable when based on serious cases.
- Salt forms are not yet normalized: `SERTRALINE` and `SERTRALINE HYDROCHLORIDE` are counted separately.
- The MedDRA hierarchy, which would allow grouping effects by organ system, requires a paid license.
- The agent was evaluated on a small set of questions and can make mistakes, which is why the SQL is always shown.
- In the demo, the 2-question limit can be bypassed by reloading the page. The real safeguard is a cap on API credits.

## Next steps

- Merge different forms of the same drug with RxNorm, the US National Library of Medicine drug reference
- Compute disproportionality measures (PRR, ROR) to detect safety signals
- Extend to medical devices with the MAUDE database
- Allow follow-up questions in the same conversation

## Stack

Python, BigQuery, dbt Core, Claude API, Streamlit, GitHub Actions

## Use and collaboration

This code is published for demonstration purposes. All rights reserved: it may not be reused, copied or adapted without my written permission.

Interested in building a similar tool on your own data? Get in touch on [LinkedIn](https://linkedin.com/in/alexandra-delverdier-65972b353).

Alexandra Delverdier, analytics engineer specialised in healthcare data