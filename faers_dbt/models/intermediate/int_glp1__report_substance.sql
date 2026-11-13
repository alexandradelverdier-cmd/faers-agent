{{ config(materialized='table') }}

-- grain : un rapport (dernière version du cas) x une substance GLP-1

with drug_lines as (

    select * from {{ ref('int_glp1__drug_lines') }}

),

reports as (

    select primaryid, caseid, fda_received_date
    from {{ ref('int_faers__reports_latest') }}

)

select
    r.primaryid,
    r.caseid,
    r.fda_received_date,
    d.substance,
    logical_or(d.is_suspect)                               as is_suspect,
    logical_or(d.is_primary_suspect)                       as is_primary_suspect,
    logical_or(d.product_type = 'single_agent')            as has_single_agent,
    logical_or(d.product_type = 'compounded')              as has_compounded,
    logical_or(d.product_type = 'insulin_combination')     as has_insulin_combination,
    count(*)                                               as nb_drug_lines
from drug_lines as d
inner join reports as r
    on d.primaryid = r.primaryid
group by 1, 2, 3, 4
