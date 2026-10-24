select
    primaryid,
    caseid,
    case outc_cod
        when 'DE' then 'death'
        when 'LT' then 'life_threatening'
        when 'HO' then 'hospitalization'
        when 'DS' then 'disability'
        when 'CA' then 'congenital_anomaly'
        when 'RI' then 'required_intervention'
        when 'OT' then 'other_serious'
    end                                            as outcome
from {{ source('faers_raw', 'outc_24q1') }}