select distinct
    re.primaryid,
    re.caseid,
    re.reaction_pt
from {{ ref('stg_faers__reactions') }} as re
inner join {{ ref('fct_reports') }} as r using (primaryid)
where re.reaction_pt is not null