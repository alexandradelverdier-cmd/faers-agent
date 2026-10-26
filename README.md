# FAERS pharmacovigilance agent

An AI agent that answers questions about adverse drug event reports received by the FDA. You ask a question in English or French, the agent writes the SQL query, runs it on BigQuery and explains the result.

Demo: [link]

## Why I built this

I worked as a nurse for nearly eight years, in hospital and then in private practice. I often saw pharmacists limited to the Vidal (the French drug reference) when looking up information on a drug. Other sources exist, though. Pharmacovigilance moves fast: reports are added, corrected or removed every day, and pharma companies, pharmacies and care facilities need easy access to them.

Later, working in medtech, I met many pharmacy professionals who were learning data skills without having been taught, in their initial training, how to work with this kind of data. I wanted to give them a tool that doesn't require learning SQL.

My background as a nurse helped at every step. I know the questions healthcare professionals ask, how little time they have, and what will actually be useful to them. It's also what helped me spot several traps in the data.

## Who it's for

Community and hospital pharmacists, pharmacovigilance teams, medical and regulatory affairs teams in pharma companies, pharmacy students. The tool is not designed for patients and gives no medical advice.

## Why not just ask ChatGPT?

A general chatbot doesn't have FAERS data. Ask it how many deaths were reported with apixaban in 2025 and it will answer from memory, with numbers that may be outdated or made up. The raw files are also far too large to drop into a conversation.

Here, every number comes from a real query on 6.4 million cleaned cases, and the query is always shown, so anyone can check where a result comes from. That matters in a regulated field. Pharmacovigilance rules are built into the agent: it focuses on the primary suspect drug, flags misuse terms and never implies causality.

FAERS is the demo, but the same approach works on an internal safety database that can't be shared with a public chatbot.

## The data: why FAERS

FAERS (FDA Adverse Event Reporting System) collects adverse event reports sent to the FDA by drug companies, healthcare professionals and patients from all over the world, including France.

It's one of the few large pharmacovigilance databases published case by case, for free, every quarter. The French national database is only publicly available in aggregated form, EudraVigilance doesn't allow full downloads, and detailed access to VigiBase (WHO) is restricted.

The project covers data from 2022 to the latest quarter published by the FDA.

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

## What gave me trouble

- **A zigzag curve.** When I looked at how reports on semaglutide evolved over time, the curve swung up and down from one quarter to the next. My first guess was a date issue: I was counting each case in the quarter of its latest update instead of its first report. I fixed it and reloaded the data, but the curve barely changed. Splitting serious and non-serious cases showed the real cause: serious cases grow steadily, while non-serious cases jump from a few dozen to several thousand between quarters. Companies have to send serious, unexpected cases quickly, but non-serious cases are often grouped into periodic reports. To judge a trend, you have to look at serious cases first, and the agent now follows that rule.
- **Duplicate versions.** An updated case shows up again in a later quarter. Out of 7.6 million raw reports, 1.1 million (about 15%) were older versions or cases withdrawn by the FDA.
- **A user outside the target audience.** A public demo can be used by anyone. When asked "Can I stop my sertraline if I feel nauseous?", the agent answered with a percentage of reports that a patient could mistake for a risk. It now runs no query for a personal situation, refers the person to their doctor or pharmacist, and mentions the French suicide prevention line (3114) when relevant.
- **Drug labels.** Combination products are written as `FENTANYL\FENTANYL CITRATE`, and the agent tended to rephrase them. It now copies labels exactly as they appear.

## Some technical choices

- **Everything as text in the raw layer.** FDA files sometimes change format. Type conversions happen in dbt, so a load doesn't fail on a badly guessed type.
- **One table per quarter.** dbt reads them all at once using BigQuery wildcard tables, so a new quarter is picked up without changing any code.
- **A load that resumes where it stopped.** The main table is loaded last and acts as a marker: an interrupted quarter is simply reloaded.
- **A free project.** Only the columns I use are loaded, and tables are partitioned and clustered to limit scanned data.
- **Agent evaluation.** A set of questions with known answers, checked against queries I wrote by hand, makes sure the agent's numbers are right.

## Data updates

The GitHub Actions workflow `update_faers.yml` loads new quarters, rebuilds the tables and runs the tests. It's triggered manually from the Actions tab. To run it automatically every month, uncomment the two `schedule` lines in the file.

## Limitations

- Reports are spontaneous: a number of reports doesn't prove causality and can't be used to compute a risk. Under-reporting and media attention also play a role.
- Companies often group non-serious cases into periodic reports, which creates artificial spikes. Trends are more reliable on serious cases.
- Salt forms aren't merged yet: `SERTRALINE` and `SERTRALINE HYDROCHLORIDE` are counted separately.
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

This code is published for demonstration purposes. All rights reserved: it may not be reused, copied or adapted without my permission.

Interested in building a similar tool on your own data? Get in touch on [LinkedIn](https://linkedin.com/in/alexandra-delverdier-65972b353).

Alexandra Delverdier, healthcare data analysts