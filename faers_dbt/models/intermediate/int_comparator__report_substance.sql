{{ config(materialized='table') }}

-- grain : un rapport (dernière version du cas) x une substance comparatrice (SGLT2, DPP-4)

with drugs as (

    select
        primaryid,
        drug_role,
        upper(concat(ifnull(drug_name, ''), ' ', ifnull(active_ingredient, ''))) as search_text
    from {{ ref('stg_faers__drugs') }}

),

comparators as (

    select * from {{ ref('comparator_drugs') }}

),

reports as (

    select primaryid, caseid, fda_received_date
    from {{ ref('int_faers__reports_latest') }}

)

select
    r.primaryid,
    r.caseid,
    r.fda_received_date,
    c.substance,
    c.drug_class,
    logical_or(d.drug_role in ('primary_suspect', 'secondary_suspect')) as is_suspect,
    logical_or(d.drug_role = 'primary_suspect')                        as is_primary_suspect
from drugs as d
inner join comparators as c
    on regexp_contains(d.search_text, concat(r'\b', c.pattern, r'\b'))
inner join reports as r
    on d.primaryid = r.primaryid
group by 1, 2, 3, 4, 5
