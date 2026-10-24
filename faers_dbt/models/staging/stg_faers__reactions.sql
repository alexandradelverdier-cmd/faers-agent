select
    primaryid,
    caseid,
    nullif(trim(pt), '')                           as reaction_pt
from {{ source('faers_raw', 'reac_24q1') }}