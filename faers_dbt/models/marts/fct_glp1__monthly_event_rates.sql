{{ config(materialized='table') }}

-- séries mensuelles pour la détection d'anomalies
-- grain : un mois x un groupe clinique

with glp1_reports as (

    select distinct
        primaryid,
        date_trunc(fda_received_date, month) as month_start
    from {{ ref('int_glp1__report_substance') }}
    where is_suspect
      and (has_single_agent or has_compounded)
      and fda_received_date >= '2022-01-01'

),

monthly_totals as (

    select month_start, count(*) as nb_reports_glp1
    from glp1_reports
    group by 1

),

clinical_groups as (

    select * from {{ ref('meddra_clinical_groups') }}

),

event_reports as (

    select distinct
        gr.primaryid,
        gr.month_start,
        cg.clinical_group
    from glp1_reports as gr
    inner join {{ ref('stg_faers__reactions') }} as rx
        on gr.primaryid = rx.primaryid
    inner join clinical_groups as cg
        on regexp_contains(lower(rx.reaction_pt), cg.include_regex)
       and not regexp_contains(lower(rx.reaction_pt), coalesce(cg.exclude_regex, r'^$'))

),

monthly_events as (

    select month_start, clinical_group, count(*) as nb_reports_event
    from event_reports
    group by 1, 2

),

-- grille complète : un mois sans déclaration doit valoir 0, pas disparaître
grid as (

    select
        t.month_start,
        t.nb_reports_glp1,
        cg.clinical_group,
        cg.label_fr
    from monthly_totals as t
    cross join clinical_groups as cg

)

select
    concat(g.clinical_group, '|', cast(g.month_start as string)) as group_month_id,
    g.month_start,
    g.clinical_group,
    g.label_fr,
    g.nb_reports_glp1,
    coalesce(e.nb_reports_event, 0) as nb_reports_event,
    round(1000 * coalesce(e.nb_reports_event, 0) / g.nb_reports_glp1, 2) as rate_per_1000
from grid as g
left join monthly_events as e
    on  g.month_start    = e.month_start
    and g.clinical_group = e.clinical_group
