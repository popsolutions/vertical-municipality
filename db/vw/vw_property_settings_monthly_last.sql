CREATE OR REPLACE VIEW public.vw_property_settings_monthly_last
AS SELECT psm.year_month,
    psm.invoice_date_due,
    psm.index_coin,
    psm.year_month_multa,
    psm.year_month_property_tax,
    psm.year_month_property_ga_tax,
    psm.year_month_property_water_consumption,
    psm.year_month_property_water_catchment,
    psm.nextread_date,
    rate_catchment,
    ar_period,
    ar_ph,
    ar_ph_limit,
    ar_uh_color,
    ar_uh_color_limit,
    ar_ut_turbidity,
    ar_ut_turbidity_limit,
    ar_chlorine_residual,
    ar_chlorine_residual_limit,
    ar_fluorides,
    ar_fluorides_limit,
    ar_ecoli,
    ar_ecoli_limit
   FROM vw_property_settings_monthly psm
  ORDER BY psm.year_month DESC
 LIMIT 1;