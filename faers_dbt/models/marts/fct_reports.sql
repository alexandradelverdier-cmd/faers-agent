with latest_reports as (
    select *
    from {{ ref('stg_faers__reports') }}
    qualify row_number() over (
        partition by caseid
        order by case_version desc, fda_received_date desc
    ) = 1
),

outcomes as (
    select
        primaryid,
        logical_or(outcome = 'death')                        as is_death,
        logical_or(outcome = 'hospitalization')              as is_hospitalization,
        string_agg(distinct outcome, ', ' order by outcome)  as outcomes
    from {{ ref('stg_faers__outcomes') }}
    group by primaryid
)

select
    r.primaryid,
    r.caseid,
    r.case_version,
    r.event_date,
    r.fda_received_date,
    r.sex,
    r.age_years,
    r.occurrence_country,
    r.reporter_type,
    o.primaryid is not null                    as is_serious,
    coalesce(o.is_death, false)                as is_death,
    coalesce(o.is_hospitalization, false)      as is_hospitalization,
    o.outcomes
from latest_reports as r
left join outcomes as o using (primaryid)