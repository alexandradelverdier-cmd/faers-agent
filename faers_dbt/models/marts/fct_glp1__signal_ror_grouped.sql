{{ config(materialized='table') }}

-- ROR par groupe clinique (plusieurs termes MedDRA regroupés)
-- grain : une molécule (ou glp1_all) x un groupe clinique

with glp1 as (

    select primaryid, substance
    from {{ ref('int_glp1__report_substance') }}
    where is_suspect
      and (has_single_agent or has_compounded)

),

exposed as (

    select primaryid, substance as drug from glp1
    union distinct
    select primaryid, 'glp1_all' as drug from glp1

),

any_glp1 as (

    select distinct primaryid from {{ ref('int_glp1__report_substance') }}

),

comparator as (

    select distinct c.primaryid
    from {{ ref('int_comparator__report_substance') }} as c
    left join any_glp1 as g
        on c.primaryid = g.primaryid
    where c.is_suspect
      and g.primaryid is null

),

study_reports as (

    select primaryid from exposed
    union distinct
    select primaryid from comparator

),

clinical_groups as (

    select * from {{ ref('meddra_clinical_groups') }}

),

reactions_grouped as (

    select distinct
        rx.primaryid,
        g.clinical_group
    from {{ ref('stg_faers__reactions') }} as rx
    inner join study_reports as s
        on rx.primaryid = s.primaryid
    inner join clinical_groups as g
        on regexp_contains(lower(rx.reaction_pt), g.include_regex)
       and not regexp_contains(lower(rx.reaction_pt), coalesce(g.exclude_regex, r'^$'))

),

exposed_totals as (

    select drug, count(distinct primaryid) as n_drug
    from exposed
    group by 1

),

comparator_total as (

    select count(*) as n_comp from comparator

),

exposed_events as (

    select e.drug, rg.clinical_group, count(distinct e.primaryid) as a
    from exposed as e
    inner join reactions_grouped as rg
        on e.primaryid = rg.primaryid
    group by 1, 2

),

comparator_events as (

    select rg.clinical_group, count(distinct c.primaryid) as c
    from comparator as c
    inner join reactions_grouped as rg
        on c.primaryid = rg.primaryid
    group by 1

),

two_by_two as (

    select
        ee.drug,
        ee.clinical_group,
        ee.a,
        et.n_drug - ee.a              as b,
        coalesce(ce.c, 0)             as c,
        ct.n_comp - coalesce(ce.c, 0) as d
    from exposed_events as ee
    inner join exposed_totals as et
        on ee.drug = et.drug
    cross join comparator_total as ct
    left join comparator_events as ce
        on ee.clinical_group = ce.clinical_group

),

ror_calc as (

    select
        *,
        safe_divide(a * d, b * c) as ror,
        sqrt(safe_divide(1, a) + safe_divide(1, b) + safe_divide(1, c) + safe_divide(1, d)) as se_ln_ror
    from two_by_two

)

select
    r.drug,
    r.clinical_group,
    g.label_fr,
    r.a,
    r.b,
    r.c,
    r.d,
    round(r.ror, 2)                                   as ror,
    round(exp(ln(r.ror) - 1.96 * r.se_ln_ror), 2)     as ror_lower_95,
    round(exp(ln(r.ror) + 1.96 * r.se_ln_ror), 2)     as ror_upper_95,
    coalesce(r.a >= 3 and exp(ln(r.ror) - 1.96 * r.se_ln_ror) > 1, false) as is_signal
from ror_calc as r
inner join clinical_groups as g
    on r.clinical_group = g.clinical_group
