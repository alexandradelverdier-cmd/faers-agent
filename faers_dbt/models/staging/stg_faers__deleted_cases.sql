select distinct trim(caseid) as caseid
from {{ source('faers_raw', 'deleted') }}
where safe_cast(trim(caseid) as int64) is not null