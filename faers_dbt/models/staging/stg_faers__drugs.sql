select
    primaryid,
    caseid,
    safe_cast(drug_seq as int64)                   as drug_seq,
    case role_cod
        when 'PS' then 'primary_suspect'
        when 'SS' then 'secondary_suspect'
        when 'C'  then 'concomitant'
        when 'I'  then 'interacting'
    end                                            as drug_role,
    upper(nullif(trim(drugname), ''))              as drug_name,
    upper(nullif(trim(prod_ai), ''))               as active_ingredient,
    nullif(trim(route), '')                        as route
from {{ source('faers_raw', 'drug') }}