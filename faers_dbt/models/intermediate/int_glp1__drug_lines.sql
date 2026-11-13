{{ config(materialized='table') }}

-- grain : une ligne médicament déclarée (primaryid x drug_seq), GLP-1 uniquement

with drugs as (

    select
        primaryid,
        caseid,
        drug_seq,
        drug_role,
        drug_name,
        active_ingredient,
        route,
        upper(concat(ifnull(drug_name, ''), ' ', ifnull(active_ingredient, ''))) as search_text
    from {{ ref('stg_faers__drugs') }}

),

brands as (

    select * from {{ ref('glp1_brands') }}

),

-- correspondance par nom de marque (OZEMPIC 1MG, ZEPBOUND KWIKPEN...)
brand_match as (

    select
        d.primaryid,
        d.drug_seq,
        b.brand,
        b.substance      as brand_substance,
        b.product_type   as brand_product_type,
        b.manufacturer,
        b.default_form
    from drugs as d
    inner join brands as b
        on regexp_contains(d.search_text, concat(r'\b', b.brand, r'\b'))
    qualify row_number() over (partition by d.primaryid, d.drug_seq order by b.brand) = 1

),

-- correspondance par substance, orthographes étrangères comprises (SEMAGLUTID, TIRZEPATID)
substance_match as (

    select
        *,
        case
            when regexp_contains(search_text, r'SEMAGLUTID')   then 'semaglutide'
            when regexp_contains(search_text, r'TIRZEPATID')   then 'tirzepatide'
            when regexp_contains(search_text, r'ORFORGLIPRON') then 'orforglipron'
            when regexp_contains(search_text, r'LIRAGLUTID')   then 'liraglutide'
            when regexp_contains(search_text, r'DULAGLUTID')   then 'dulaglutide'
            when regexp_contains(search_text, r'EXENATID')     then 'exenatide'
            when regexp_contains(search_text, r'LIXISENATID')  then 'lixisenatide'
        end as name_substance
    from drugs

)

select
    s.primaryid,
    s.caseid,
    s.drug_seq,
    s.drug_role,
    s.drug_name,
    s.active_ingredient,
    s.route,
    coalesce(s.name_substance, bm.brand_substance) as substance,
    bm.brand,
    bm.manufacturer,
    case
        when bm.default_form in ('injectable', 'oral') then bm.default_form
        when regexp_contains(upper(ifnull(s.route, '')), r'^ORAL')          then 'oral'
        when regexp_contains(upper(ifnull(s.route, '')), r'^SUBCUT|INJECT') then 'injectable'
    end as dosage_form,
    case
        when bm.brand_product_type = 'insulin_combination'
          or regexp_contains(s.search_text, r'INSULIN (GLARGINE|DEGLUDEC)')
            then 'insulin_combination'
        when regexp_contains(s.search_text, r'COBALAMIN|PYRIDOXINE|NIACINAMIDE|GLYCINE|CARNITINE|NADIDE|COMPOUND')
            then 'compounded'
        else 'single_agent'
    end as product_type,
    s.drug_role in ('primary_suspect', 'secondary_suspect') as is_suspect,
    s.drug_role = 'primary_suspect' as is_primary_suspect
from substance_match as s
left join brand_match as bm
    on  s.primaryid = bm.primaryid
    and s.drug_seq  = bm.drug_seq
where coalesce(s.name_substance, bm.brand_substance) is not null