select
    d.primaryid,
    d.caseid,
    d.drug_seq,
    d.drug_role,
    d.drug_name,
    d.active_ingredient,
    d.route
from {{ ref('stg_faers__drugs') }} as d
inner join {{ ref('fct_reports') }} as r using (primaryid)