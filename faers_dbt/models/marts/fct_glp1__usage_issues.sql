{{ config(materialized='table') }}

-- erreurs d'administration et inefficacité ressentie, par marque, forme et trimestre
-- grain : une marque x une forme (injectable / oral) x un trimestre

with lines as (

    select distinct
        primaryid,
        brand,
        substance,
        manufacturer,
        dosage_form
    from {{ ref('int_glp1__drug_lines') }}
    where is_suspect
      and brand is not null
      and dosage_form is not null
      and product_type != 'insulin_combination'

),

reports as (

    select
        primaryid,
        date_trunc(fda_received_date, quarter) as quarter_start
    from {{ ref('int_faers__reports_latest') }}
    where fda_received_date is not null

),

usage_terms as (

    select * from {{ ref('meddra_usage_issues') }}

),

report_flags as (

    select
        rx.primaryid,
        logical_or(u.usage_category = 'administration_error') as has_admin_error,
        logical_or(u.usage_category = 'perceived_inefficacy') as has_perceived_inefficacy
    from {{ ref('stg_faers__reactions') }} as rx
    inner join usage_terms as u
        on rx.reaction_pt = u.reaction_pt
    group by 1

),

aggregated as (

    select
        l.brand,
        l.substance,
        l.manufacturer,
        l.dosage_form,
        r.quarter_start,
        count(*)                                              as nb_reports,
        countif(coalesce(f.has_admin_error, false))           as nb_reports_admin_error,
        countif(coalesce(f.has_perceived_inefficacy, false))  as nb_reports_perceived_inefficacy
    from lines as l
    inner join reports as r
        on l.primaryid = r.primaryid
    left join report_flags as f
        on l.primaryid = f.primaryid
    group by 1, 2, 3, 4, 5

)

select
    concat(brand, '|', dosage_form, '|', cast(quarter_start as string)) as brand_form_quarter_id,
    *
from aggregated
