{{ config(materialized='table') }}

-- ROR par groupe clinique, avec analyse de sensibilité
-- grain : une analyse x une molécule (ou glp1_all) x un groupe clinique
-- analysis = all_suspect (suspect principal ou secondaire) ou primary_suspect (suspect principal seul)

with glp1_lines as (

    select primaryid, substance, is_suspect, is_primary_suspect
    from {{ ref('int_glp1__report_substance') }}
    where has_single_agent or has_compounded

),

exposed as (

    select 'all_suspect' as analysis, primaryid, substance as drug from glp1_lines where is_suspect
    union distinct
    select 'all_suspect', primaryid, 'glp1_all' from glp1_lines where is_suspect
    union distinct
    select 'primary_suspect', primaryid, substance from glp1_lines where is_primary_suspect
    union distinct
    select 'primary_suspect', primaryid, 'glp1_all' from glp1_lines where is_primary_suspect

),

any_glp1 as (

    select distinct primaryid from {{ ref('int_glp1__report_substance') }}

),

comparator_lines as (

    select c.primaryid, c.is_suspect, c.is_primary_suspect
    from {{ ref('int_comparator__report_substance') }} as c
    left join any_glp1 as g
        on c.primaryid = g.primaryid
    where g.primaryid is null

),

comparator as (

    select distinct 'all_suspect' as analysis, primaryid from comparator_lines where is_suspect
    union distinct
    select distinct 'primary_suspect', primaryid from comparator_lines where is_primary_suspect

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

    select analysis, drug, count(distinct primaryid) as n_drug
    from exposed
    group by 1, 2

),

comparator_totals as (

    select analysis, count(distinct primaryid) as n_comp
    from comparator
    group by 1

),

exposed_events as (

    select e.analysis, e.drug, rg.clinical_group, count(distinct e.primaryid) as a
    from exposed as e
    inner join reactions_grouped as rg
        on e.primaryid = rg.primaryid
    group by 1, 2, 3

),

comparator_events as (

    select c.analysis, rg.clinical_group, count(distinct c.primaryid) as c
    from comparator as c
    inner join reactions_grouped as rg
        on c.primaryid = rg.primaryid
    group by 1, 2

),

two_by_two as (

    select
        ee.analysis,
        ee.drug,
        ee.clinical_group,
        ee.a,
        et.n_drug - ee.a              as b,
        coalesce(ce.c, 0)             as c,
        ct.n_comp - coalesce(ce.c, 0) as d
    from exposed_events as ee
    inner join exposed_totals as et
        on  ee.analysis = et.analysis
        and ee.drug     = et.drug
    inner join comparator_totals as ct
        on ee.analysis = ct.analysis
    left join comparator_events as ce
        on  ee.analysis       = ce.analysis
        and ee.clinical_group = ce.clinical_group

),

ror_calc as (

    select
        *,
        safe_divide(a * d, b * c) as ror,
        sqrt(safe_divide(1, a) + safe_divide(1, b) + safe_divide(1, c) + safe_divide(1, d)) as se_ln_ror
    from two_by_two

)

select
    r.analysis,
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