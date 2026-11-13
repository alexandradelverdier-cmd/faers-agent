{{ config(materialized='table') }}

-- disproportionnalité (ROR) : GLP-1 suspects vs comparateur actif (SGLT2 + DPP-4)
-- grain : une molécule (ou glp1_all) x un effet indésirable (MedDRA PT)

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

reactions as (

    select distinct primaryid, trim(reaction_pt) as reaction_pt
    from {{ ref('stg_faers__reactions') }}
    where reaction_pt is not null

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

    select e.drug, rx.reaction_pt, count(distinct e.primaryid) as a
    from exposed as e
    inner join reactions as rx
        on e.primaryid = rx.primaryid
    group by 1, 2

),

comparator_events as (

    select rx.reaction_pt, count(distinct c.primaryid) as c
    from comparator as c
    inner join reactions as rx
        on c.primaryid = rx.primaryid
    group by 1

),

two_by_two as (

    select
        ee.drug,
        ee.reaction_pt,
        ee.a,
        et.n_drug - ee.a              as b,
        coalesce(ce.c, 0)             as c,
        ct.n_comp - coalesce(ce.c, 0) as d
    from exposed_events as ee
    inner join exposed_totals as et
        on ee.drug = et.drug
    cross join comparator_total as ct
    left join comparator_events as ce
        on ee.reaction_pt = ce.reaction_pt

),

ror_calc as (

    select
        *,
        safe_divide(a * d, b * c) as ror,
        sqrt(safe_divide(1, a) + safe_divide(1, b) + safe_divide(1, c) + safe_divide(1, d)) as se_ln_ror
    from two_by_two

)

select
    drug,
    reaction_pt,
    a,
    b,
    c,
    d,
    round(ror, 2)                                 as ror,
    round(exp(ln(ror) - 1.96 * se_ln_ror), 2)     as ror_lower_95,
    round(exp(ln(ror) + 1.96 * se_ln_ror), 2)     as ror_upper_95,
    coalesce(a >= 3 and exp(ln(ror) - 1.96 * se_ln_ror) > 1, false) as is_signal
from ror_calc
