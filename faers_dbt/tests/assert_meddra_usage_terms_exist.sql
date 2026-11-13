-- échoue si un terme du seed meddra_usage_issues est absent des réactions déclarées
select s.reaction_pt
from {{ ref('meddra_usage_issues') }} as s
left join (
    select distinct reaction_pt from {{ ref('stg_faers__reactions') }}
) as rx
    on s.reaction_pt = rx.reaction_pt
where rx.reaction_pt is null
