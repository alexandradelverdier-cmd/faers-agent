{{ config(materialized='table') }}

-- une seule version par cas (la plus récente), cas supprimés par la FDA exclus

with reports as (

    select * from {{ ref('stg_faers__reports') }}

),

deleted_cases as (

    select distinct caseid from {{ ref('stg_faers__deleted_cases') }}

),

latest_version as (

    select *
    from reports
    qualify row_number() over (
        partition by caseid
        order by
            fda_received_date desc,
            case_version desc,
            source_quarter desc,
            safe_cast(primaryid as int64) desc
    ) = 1

)

select l.*
from latest_version as l
left join deleted_cases as d
    on l.caseid = d.caseid
where d.caseid is null
