alter table property_water_catchment_monthly_rate drop constraint property_water_catchment_monthly_rate_property_water_catchment_;

drop view vw_property_land_lasts_ids;

drop view vw_property_settings_monthly_last;

drop view vw_property_settings_monthly;

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

CREATE OR REPLACE VIEW public.vw_property_land_lasts_ids
AS SELECT t.land_id,
    t.year_month,
    t.property_tax_id,
    ptx.date AS property_tax_date,
    t.property_ga_tax_id,
    pga.date AS property_ga_tax_date,
    t.property_water_consumption_id,
    pwc.date AS property_water_consumption_date,
    t.property_water_catchment_id,
    pcc.date AS property_water_catchment_date
   FROM ( SELECT l.id AS land_id,
            ( SELECT p.id
                   FROM property_tax p
                  WHERE p.land_id = l.id AND anomes(p.date) = sml.year_month_property_tax
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_tax_id,
            ( SELECT p.id
                   FROM property_ga_tax p
                  WHERE p.land_id = l.id AND anomes(p.date::timestamp without time zone) = sml.year_month_property_ga_tax
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_ga_tax_id,
            ( SELECT p.id
                   FROM property_water_consumption p
                  WHERE p.land_id = l.id AND anomes(p.date::timestamp without time zone) = sml.year_month_property_water_consumption
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_water_consumption_id,
            ( SELECT p.id
                   FROM property_water_catchment p
                  WHERE p.land_id = l.id AND anomes(p.date::timestamp without time zone) = sml.year_month_property_water_catchment
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_water_catchment_id,
            sml.year_month
           FROM property_land l,
            vw_property_settings_monthly_last sml) t
     LEFT JOIN property_tax ptx ON ptx.id = t.property_tax_id
     LEFT JOIN property_ga_tax pga ON pga.id = t.property_ga_tax_id
     LEFT JOIN property_water_consumption pwc ON pwc.id = t.property_water_consumption_id
     LEFT JOIN property_water_catchment pcc ON pcc.id = t.property_water_catchment_id;

drop table property_settings_monthly;

