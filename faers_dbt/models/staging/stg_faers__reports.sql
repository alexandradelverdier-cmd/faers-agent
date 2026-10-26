select
    primaryid,
    caseid,
    safe_cast(caseversion as int64)                as case_version,
    concat('20', substr(_table_suffix, 1, 2), '-Q', substr(_table_suffix, 4, 1)) as source_quarter,
    safe.parse_date('%Y%m%d', event_dt)            as event_date,
    safe.parse_date('%Y%m%d', fda_dt)              as fda_received_date,
    nullif(trim(sex), '')                          as sex,
    case nullif(age_cod, '')
        when 'YR'  then safe_cast(age as float64)
        when 'DEC' then safe_cast(age as float64) * 10
        when 'MON' then safe_cast(age as float64) / 12
        when 'WK'  then safe_cast(age as float64) / 52
        when 'DY'  then safe_cast(age as float64) / 365
        when 'HR'  then safe_cast(age as float64) / 8760
    end                                            as age_years,
    nullif(trim(occr_country), '')                 as occurrence_country,
    nullif(trim(occp_cod), '')                     as reporter_type
from {{ source('faers_raw', 'demo') }}