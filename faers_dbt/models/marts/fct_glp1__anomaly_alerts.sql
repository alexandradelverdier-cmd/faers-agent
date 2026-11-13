{{
  config(
    materialized='table',
    pre_hook="""
      create or replace model `{{ target.project }}.{{ target.dataset }}.glp1_event_rate_arima`
      options (
        model_type                = 'ARIMA_PLUS',
        time_series_timestamp_col = 'month_start',
        time_series_data_col      = 'rate_per_1000',
        time_series_id_col        = 'clinical_group',
        data_frequency            = 'MONTHLY'
      ) as
      select month_start, clinical_group, rate_per_1000
      from {{ ref('fct_glp1__monthly_event_rates') }}
      where month_start <= (
        select date_sub(max(month_start), interval 6 month)
        from {{ ref('fct_glp1__monthly_event_rates') }}
      )
    """
  )
}}

-- veille automatique : le modèle ARIMA_PLUS est entraîné sur tout l'historique
-- sauf les 6 derniers mois, puis ces 6 mois lui sont présentés comme des données nouvelles
-- grain : un groupe clinique x un mois de la fenêtre de surveillance

with monitoring_window as (

    select month_start, clinical_group, rate_per_1000
    from {{ ref('fct_glp1__monthly_event_rates') }}
    where month_start > (
        select date_sub(max(month_start), interval 6 month)
        from {{ ref('fct_glp1__monthly_event_rates') }}
    )

),

detection as (

    select *
    from ml.detect_anomalies(
        model `{{ target.project }}.{{ target.dataset }}.glp1_event_rate_arima`,
        struct(0.95 as anomaly_prob_threshold),
        (select * from monitoring_window)
    )

)

select
    concat(clinical_group, '|', cast(date(month_start) as string)) as group_month_id,
    clinical_group,
    date(month_start)                                  as month_start,
    rate_per_1000,
    round(lower_bound, 2)                              as lower_bound,
    round(upper_bound, 2)                              as upper_bound,
    round(safe_divide(rate_per_1000, upper_bound), 2)  as intensity,
    round(anomaly_probability, 3)                      as anomaly_probability,
    coalesce(is_anomaly and rate_per_1000 > upper_bound, false) as is_alert
from detection
