CREATE OR REPLACE VIEW public.vw_property_settings_monthly
AS SELECT psm.year_month,
    (((("substring"(psm.year_month::character varying::text, 1, 4) || '-'::text) || "substring"(psm.year_month::character varying::text, 5, 4)) || '-'::text) || '10'::text)::date AS invoice_date_due,
    psm.index_coin,
    anomes_inc(psm.year_month, yfi.multa) AS year_month_multa,
    anomes_inc(psm.year_month, yfi.property_tax) AS year_month_property_tax,
    anomes_inc(psm.year_month, yfi.property_ga_tax) AS year_month_property_ga_tax,
    anomes_inc(psm.year_month, yfi.property_water_consumption) AS year_month_property_water_consumption,
    anomes_inc(psm.year_month, yfi.property_water_catchment) AS year_month_property_water_catchment,
    psm.nextread_date,
    psm.ar_period,
    psm.ar_ph,
    psm.ar_ph_limit,
    psm.ar_uh_color,
    psm.ar_uh_color_limit,
    psm.ar_ut_turbidity,
    psm.ar_ut_turbidity_limit,
    psm.ar_chlorine_residual,
    psm.ar_chlorine_residual_limit,
    psm.ar_fluorides,
    psm.ar_fluorides_limit,
    psm.ar_ecoli,
    psm.ar_ecoli_limit,
    psm.rate_catchment
   FROM property_water_catchment_monthly_rate psm,
    vw_product_template_yearmonth_dec_from_invoice yfi
  ORDER BY psm.year_month DESC;