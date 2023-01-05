CREATE OR REPLACE VIEW public.vw_property_settings_monthly_last
AS SELECT psm.year_month,
    psm.invoice_date_due,
    psm.index_coin,
    psm.year_month_multa,
    psm.year_month_property_tax,
    psm.year_month_property_ga_tax,
    psm.year_month_property_water_consumption,
    psm.year_month_property_water_catchment,
    psm.nextread_date
   FROM vw_property_settings_monthly psm
  ORDER BY psm.year_month DESC
 LIMIT 1;